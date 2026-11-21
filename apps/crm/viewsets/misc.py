from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone as tz, translation
from django.utils.translation import gettext as _

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from crm.forms import ExtraFieldForm
from crm.models import Note, Upload, Tag, ItemsExport, ExtraField
from crm.tasks import export_items
from crm.utils import get_batch_qs


__all__ = (
    'TagsViewSet',
    'NotesViewSet',
    'UploadsViewSet',
    'ExtraFieldsViewSet',
    'ItemsExportViewSet',
)


class NotesViewSet(GenericViewSet):
    def list(self, request):
        data = request.query_params

        notes = Note.objects.by_account(request.account)
        if not self.request.user_link.has_perm('view_all_note'):
            notes = notes.filter(user=self.request.user)

        content_type = data.get('content_type__model')
        if content_type:
            notes = notes.filter(content_type__model=content_type)

        item_id = data.get('item_id')
        if item_id:
            notes = notes.filter(item_id=item_id)

        return Response([note.serialize() for note in notes])

    @action(detail=True, methods=['POST'])
    def delete(self, request, pk):
        note = Note.objects.by_account(request.account).filter(id=pk).first()
        if not note:
            return Response({}, status=404)
        for upload in Upload.objects.by_account(request.account).filter(note_id=pk):
            Upload.archive(ids=[upload.id])

        Note.archive(ids=[pk])
        return Response({})


class UploadsViewSet(GenericViewSet):
    def list(self, request):
        data = request.query_params

        uploads = Upload.objects.by_account(request.account)
        if not self.request.user_link.has_perm('view_all_note'):
            uploads = uploads.filter(user=self.request.user)

        content_type = data.get('content_type__model')
        if content_type:
            uploads = uploads.filter(content_type__model=content_type)

        item_id = data.get('item_id')
        if item_id:
            uploads = uploads.filter(item_id=item_id)

        return Response([upload.serialize() for upload in uploads])

    @action(detail=True, methods=['POST'])
    def delete(self, request, pk):
        upload = Upload.objects.by_account(request.account).filter(id=pk).first()
        if not upload:
            return Response({}, status=404)
        Upload.archive(ids=[upload.pk])
        return Response({})


class ItemsExportViewSet(GenericViewSet):
    def create(self, request):
        data = request.data

        extension = data['extension']
        model_name = data['model_name']

        model = apps.get_model('crm', model_name)
        qs = get_batch_qs(model, data=data).by_account(request.account)

        items_export = ItemsExport.objects.create(
            account=request.account,
            user=request.user,
            model_name=model_name,
            extension=extension,
            item_ids=list(qs.values_list('id', flat=True))
        )

        export_items.delay(request.account.id, items_export.id)

        return Response({
            'items_export_id': items_export.id,
        })

    def retrieve(self, request, pk):
        try:
            items_export = ItemsExport.objects.by_account(request.account).get(user=request.user, id=pk)
        except ItemsExport.DoesNotExist:
            return Response({})

        if not items_export.is_ready:
            return Response({
                'is_ready': False,
            })

        return Response({
            'is_ready': True,
            'url': items_export.result.url,
        })


class ExtraFieldsViewSet(GenericViewSet):
    def list(self, request):
        extra_fields = ExtraField.objects.by_account(request.account).select_related('content_type')

        content_type = request.query_params.get('content_type__model')
        if content_type:
            extra_fields = extra_fields.filter(content_type__model=content_type)

        return Response([extra_field.serialize() for extra_field in extra_fields])

    @action(detail=False, methods=['POST'])
    def add(self, request):
        data = request.data

        content_type = ContentType.objects.get(model=data.get('content_type'))

        form = ExtraFieldForm(data=data, content_type=content_type)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        cd = form.cleaned_data

        extra_field = ExtraField.objects.create(
            account=request.account,
            content_type=content_type,
            name=cd['name'],
            type=data['type'],
            select_options=data.get('select_options')
        )

        return Response({
            'extra_field': extra_field.serialize(),
        })

    @action(detail=True, methods=['POST'])
    def edit(self, request, pk):
        try:
            extra_field = ExtraField.objects.by_account(request.account).get(id=pk)
        except ExtraField.DoesNotExist:
            return Response({
                'error': _('This field does not exist')
            }, status=400)

        data = request.data

        form = ExtraFieldForm(data=data, instance=extra_field)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        cd = form.cleaned_data

        extra_field.name = cd['name']
        extra_field.select_options = data.get('select_options')

        extra_field.save()

        return Response({
            'extra_field': extra_field.serialize(),
        })

    @action(detail=True, methods=['POST'])
    def delete(self, request, pk):
        try:
            extra_field = ExtraField.objects.by_account(request.account).get(id=pk)
        except ExtraField.DoesNotExist:
            return Response({'error': _('This field does not exist')}, status=400)

        extra_field.archive()

        return Response({})

    @action(detail=True, methods=['POST'])
    def change_is_required(self, request, pk):
        try:
            extra_field = ExtraField.objects.by_account(request.account).get(id=pk)
        except ExtraField.DoesNotExist:
            return Response({'error': _('This field does not exist')}, status=400)

        extra_field.is_required = not extra_field.is_required
        extra_field.updated_at = tz.now()
        extra_field.save(update_fields=('is_required', 'updated_at'))

        return Response({})


class TagsViewSet(GenericViewSet):
    def list(self, request):
        query_params = request.query_params

        tags = Tag.objects.by_account(request.account)

        search = query_params.get('search')
        if search:
            tags = tags.filter(name__icontains=search)

        is_settings = query_params.get('is_settings')
        if is_settings:
            data = [tag.serialize(is_settings=True) for tag in self.paginate_queryset(tags)]
            return self.get_paginated_response(data)

        return Response([tag.serialize() for tag in tags])

    def create(self, request):
        data = request.data

        name = data.get('name')
        if not name:
            return Response({'error': _('Invalid request')}, status=400)

        if Tag.objects.by_account(request.account).filter(name__iexact=name).exists():
            return Response({'error': _('A tag with this name already exists')}, status=400)

        tag = Tag.objects.create(account=request.account, name=name)

        return Response({
            'tag': tag.serialize(is_settings=True),
        })

    @action(detail=True, methods=['POST'])
    def edit(self, request, pk):
        data = request.data

        try:
            tag = Tag.objects.by_account(request.account).get(id=pk)
        except Tag.DoesNotExist:
            return Response({'error': _('This tag does not exist')}, status=400)

        name = data.get('value')
        if not name:
            return Response({'error': _('Invalid request')}, status=400)

        if Tag.objects.by_account(request.account).filter(name__iexact=name).exclude(pk=tag.pk).exists():
            return Response({'error': _('A tag with this name already exists')}, status=400)

        tag.name = name
        tag.updated_at = tz.now()
        tag.save(update_fields=('name', 'updated_at'))

        return Response({})

    @action(detail=True, methods=['POST'])
    def delete(self, request, pk):
        try:
            tag = Tag.objects.by_account(request.account).get(id=pk)
        except Tag.DoesNotExist:
            return Response({'error': _('The tag has already been deleted')}, status=400)

        tag.delete()

        return Response({})
