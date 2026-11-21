import operator
from collections import defaultdict
from functools import reduce

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext as _

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.utils import as_int

from accounts.models import get_user_account_name
from crm.mixins import ErrorResponseMixin, EditMTMFieldsMixin
from crm.models import (
    Activity, Task, Note, Upload, Tag, ExtraField, ItemResponsibleLink, ItemTagLink, ItemExtraFieldLink,
)
from crm.tasks import notify_responsibles, archive_items, set_remind_task_links
from notifications.helpers import NotificationsHelper


class ItemViewSet(ErrorResponseMixin, EditMTMFieldsMixin, GenericViewSet):
    model = None
    queryset = None
    filterset_class = None
    search_fields = []

    @staticmethod
    def _get_account_responsibles(account, responsible_ids):
        responsible_ids = {user_id for user_id in map(as_int, responsible_ids) if user_id}
        responsibles = User.objects.filter(
            useraccountlink__account=account,
            useraccountlink__is_active=True,
            id__in=responsible_ids,
        ).distinct()
        if set(responsibles.values_list('id', flat=True)) != responsible_ids:
            raise ValidationError({'error': _('Invalid request')})
        return responsibles

    def get_queryset(self):
        if self.queryset is None:
            return self.model.objects.by_account(self.request.account)
        return super().get_queryset()

    def _get_batch_qs(self, data):
        qs = self.get_queryset()

        query = data.get('query')
        if query:
            qs = self.filterset_class(query, qs).qs

            search = query.get('search')
            if search:
                qs = qs.filter(
                    reduce(
                        operator.or_,
                        (Q(**{'{}__icontains'.format(field): search}) for field in self.search_fields)
                    )
                )

        item_ids = data.get('item_ids')
        if item_ids:
            qs = qs.filter(id__in=item_ids)

        return qs

    def order_queryset(self, qs):
        ordering = self.request.query_params.get('ordering')
        if ordering:
            if 'expire_date' in ordering:
                qs = qs.extra(
                    select={'null_expire_date': 'CASE WHEN crm_task.expire_date IS NULL THEN 0 ELSE 1 END'}
                ).order_by('{}null_expire_date'.format('-' if '-' in ordering else ''), ordering)
            elif 'extra_field' in ordering:
                field_id = ordering.split('extra_field_')[1]

                field_name = 'value'
                try:
                    field = ExtraField.objects.by_account(self.request.account).get(id=field_id)
                except ExtraField.DoesNotExist:
                    pass
                else:
                    if field.is_number:
                        field_name = 'number_value'
                    elif field.is_dt:
                        field_name = 'dt_value'

                qs = qs.extra(
                    select={
                        'extra_field_value': """
                            SELECT link.{}
                            FROM crm_{}extrafieldlink AS link
                            WHERE link.field_id={} AND link.{}_id=crm_{}.id
                        """.format(field_name, self.model.ITEM_TYPE, field_id, self.model.ITEM_TYPE, self.model.ITEM_TYPE)
                    }
                ).order_by('{}extra_field_value'.format('-' if '-' in ordering else ''))

        return qs

    def list(self, request, *args, **kwargs):
        """
        Overrides generic list method. Adds using of order_queryset for complex ordering.
        """
        qs = self.filter_queryset(self.get_queryset())
        qs = self.order_queryset(qs)

        page = self.paginate_queryset(qs)
        if page:
            item_ids = [item.id for item in page]

            serialize_params = {
                'request': request,
                'responsible_links_map': self.get_responsible_links_map(self.model.ITEM_TYPE, item_ids),
                'tag_links_map': self.get_tag_links_map(self.model.ITEM_TYPE, item_ids),
                'extra_field_links_map': self.get_extra_field_links_map(self.model.ITEM_TYPE, item_ids),
            }

            data = [item.serialize(**serialize_params) for item in page]
            return self.get_paginated_response(data)

        # when request without page_size param
        # TODO: find out, when this happens
        item_ids = list(qs.values_list('id', flat=True))

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(self.model.ITEM_TYPE, item_ids),
            'tag_links_map': self.get_tag_links_map(self.model.ITEM_TYPE, item_ids),
            'extra_field_links_map': self.get_extra_field_links_map(self.model.ITEM_TYPE, item_ids),
        }

        data = [item.serialize(**serialize_params) for item in qs]

        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        item = self.get_object()

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(self.model.ITEM_TYPE, [item.id]),
            'tag_links_map': self.get_tag_links_map(self.model.ITEM_TYPE, [item.id]),
            'extra_field_links_map': self.get_extra_field_links_map(self.model.ITEM_TYPE, [item.id]),
        }
        if self.model == Task:
            serialize_params['is_retrieve'] = True

        data = item.serialize(**serialize_params)

        return Response(data)

    @action(detail=False, methods=['post'])
    def batch_edit_responsibles(self, request):
        data = request.data

        qs = self._get_batch_qs(data)
        if not qs:
            return Response({
                'error': _('Nothing selected for modification')
            }, status=400)

        action = data.get('action')
        if not action:
            return self.get_error_response(_('No action selected.'))

        responsibles = data.get('responsibles') or []
        if responsibles:
            responsibles = self._get_account_responsibles(request.account, responsibles)

        for item in qs:
            old_responsible_ids = item.get_responsible_ids()
            self.update_items_responsibles(
                item.ITEM_TYPE, [item.id], [responsible.id for responsible in responsibles], action
            )
            notify_responsibles.delay(
                request.account.id, item.ITEM_TYPE, item.id, old_responsible_ids, request.user_link.name
            )
            if item.ITEM_TYPE == 'task':
                set_remind_task_links.delay(request.account.id, item.id)

        return Response({})

    @action(detail=False, methods=['post'])
    def batch_edit_tags(self, request):
        data = request.data

        qs = self._get_batch_qs(data)
        if not qs:
            return Response({
                'error': _('Nothing selected for modification')
            }, status=400)

        action = data.get('action')
        if not action:
            return self.get_error_response(_('No action selected.'))

        tags = data.get('tags') or []
        tags = [Tag.objects.get_or_create(account=request.account, name=tag)[0] for tag in tags if isinstance(tag, str)]

        for item in qs:
            self.update_items_tags(item.ITEM_TYPE, [item.id], [tag.id for tag in tags], action)

        return Response({})

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        item_ids = list(self._get_batch_qs(request.data).values_list('id', flat=True))
        if not item_ids:
            return Response({'error': _('Nothing selected for deletion')}, status=400)

        archive_items.delay(request.account.id, self.model._meta.model_name, item_ids)

        return Response({})

    @action(detail=True, methods=['post'])
    def edit_responsibles(self, request, pk):
        responsible_ids = [user_id for user_id in map(as_int, request.POST.getlist('value[]')) if user_id]
        if not responsible_ids:
            return Response({'success': True, 'responsibles': []})

        item = self.get_object()
        responsibles = self._get_account_responsibles(request.account, responsible_ids)

        old_responsible_ids = item.get_responsible_ids()
        self.update_items_responsibles(
            item.ITEM_TYPE, [item.id], [responsible.id for responsible in responsibles], 'set'
        )
        notify_responsibles.delay(request.account.id, item.ITEM_TYPE, item.id, old_responsible_ids, request.user_link.name)
        if item.ITEM_TYPE == 'task':
            set_remind_task_links.delay(request.account.id, item.id)

        return Response({
            'success': True,
            'responsibles': [{
                'id': responsible.id,
                'name': get_user_account_name(request.account, responsible),
            } for responsible in responsibles]
        })

    @action(detail=True, methods=['post'])
    def edit_tags(self, request, pk):
        tags = request.POST.getlist('value[]')
        if not tags:
            return Response({'success': True, 'tags': []})

        item = self.get_object()
        tags = [Tag.objects.get_or_create(account=request.account, name=tag)[0] for tag in tags]
        self.update_items_tags(item.ITEM_TYPE, [item.id], [tag.id for tag in tags], 'set')

        return Response({
            'success': True,
            'tags': [tag.serialize() for tag in tags],
        })

    @action(detail=True, methods=['post'])
    def delete(self, request, pk):
        item = self.get_object()
        self.model.archive([item.pk])
        return Response({})

    @staticmethod
    def handle_upload_files(upload_files, item, user, note=None):
        content_type = item.get_content_type()

        uploads = []
        for upload_file in upload_files:
            upload_name = upload_file.name
            if Upload.all_objects.by_account(item.account).filter(
                name=upload_file.name,
                item_id=item.id,
                content_type=content_type
            ).exists():
                postfix = 2
                while True:
                    name_parts = upload_name.split('.', 1)
                    if len(name_parts) == 1:
                        new_name = '{} {}'.format(name_parts[0], postfix)
                    else:
                        new_name = '{} {}.{}'.format(name_parts[0], postfix, name_parts[1])

                    if Upload.all_objects.by_account(item.account).filter(
                        name=new_name,
                        item_id=item.id,
                        content_type=content_type
                    ).exists():
                        postfix += 1
                    else:
                        upload_name = new_name
                        break

            if upload_file.size > settings.UPLOAD_FILE_MAX_SIZE:
                return None, _('Maximum file size is {} MB').format(settings.UPLOAD_FILE_MAX_SIZE_MB)

            try:
                uploads_size = sum([upload.file.size for upload in Upload.objects.by_account(item.account)])
            except AttributeError:
                uploads_size = 0

            if upload_file and uploads_size + upload_file.size > settings.TOTAL_UPLOADS_LIMIT:
                return None, _('The file storage limit has been reached')

            upload = Upload.objects.create(
                account=item.account,
                user=user,
                item=item,
                name=upload_name,
                file=upload_file,
                note=note
            )
            Activity.log_addition(upload)
            uploads.append(upload)

        return uploads, None

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk):
        data = request.data

        user = request.user
        item = self.get_object()

        text = data['text']
        if not text:
            return Response({'error': _('Enter note text')}, status=400)

        with transaction.atomic():
            note = Note.objects.create(
                account=request.account,
                user=user,
                item=item,
                text=text
            )
            Activity.log_addition(note)

            responsible_ids = set(item.get_responsible_ids() + [item.user_id]) - {note.user_id}
            responsibles = User.objects.filter(is_active=True, id__in=responsible_ids)
            for responsible in responsibles:
                NotificationsHelper.crm.note_added(request.account, responsible, note, item.ITEM_TYPE)

            upload_files = []
            for key, value in request.data.items():
                if 'file_' in key:
                    upload_files.append(value)

            if upload_files:
                uploads, error = self.handle_upload_files(upload_files, item, user, note)
                if error:
                    return Response({'error': error}, status=400)

        return Response({
            'note': note.serialize(),
        })

    @action(detail=True, methods=['post'])
    def add_upload(self, request, pk):
        item = self.get_object()

        upload_files = []
        for key, value in request.data.items():
            if 'file_' in key:
                upload_files.append(value)

        if not upload_files:
            return Response({'error': _('Invalid request')}, status=400)

        uploads, error = self.handle_upload_files(upload_files, item, request.user)
        if error:
            return Response({'error': error}, status=400)

        return Response({
            'uploads': [upload.serialize() for upload in uploads],
        })

    def get_responsible_links_map(self, item_type, item_ids):
        responsible_links = ItemResponsibleLink.objects.by_account(self.request.account).select_related('user').filter(
            item_type=item_type,
            item_id__in=item_ids
        )
        links_map = defaultdict(list)
        for link in responsible_links:
            links_map[link.item_id].append(link)
        return links_map

    def get_tag_links_map(self, item_type, item_ids):
        tag_links = ItemTagLink.objects.by_account(self.request.account).select_related('tag').filter(
            item_type=item_type,
            item_id__in=item_ids
        )
        links_map = defaultdict(list)
        for link in tag_links:
            links_map[link.item_id].append(link)
        return links_map

    def get_extra_field_links_map(self, item_type, item_ids):
        tag_links = ItemExtraFieldLink.objects.by_account(self.request.account).select_related('field').filter(
            item_type=item_type,
            item_id__in=item_ids
        )
        links_map = defaultdict(list)
        for link in tag_links:
            links_map[link.item_id].append(link)
        return links_map
