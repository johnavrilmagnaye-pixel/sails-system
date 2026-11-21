from django.contrib.auth.mixins import AccessMixin
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import UserAccountLink
from crm.helpers import ItemsHelper
from crm.models import ItemResponsibleLink, ItemTagLink, Tag


class ErrorResponseMixin(object):
    @staticmethod
    def get_error_response(msg):
        return Response({'error': msg}, status=400)


class EditMTMFieldsMixin(object):
    ACTION_ADD = 'add'
    ACTION_SET = 'set'
    ACTION_REMOVE = 'remove'

    RESPONSIBLE_FIELD_NAME = 'user_id'
    TAG_FIELD_NAME = 'tag_id'

    def _validate_link_ids(self, item_type, link_field_name, item_ids, mtm_ids):
        account = self.request.account
        item_ids = set(item_ids)
        mtm_ids = set(mtm_ids)
        item_model = ItemsHelper.get_model(item_type)
        if item_model is None or set(
            item_model.all_objects.filter(account=account, id__in=item_ids).values_list('id', flat=True)
        ) != item_ids:
            raise ValidationError({'error': _('Invalid request')})

        if link_field_name == self.RESPONSIBLE_FIELD_NAME:
            valid_ids = set(UserAccountLink.objects.filter(
                account=account,
                user_id__in=mtm_ids,
                is_active=True,
                user__is_active=True,
            ).values_list('user_id', flat=True))
        else:
            valid_ids = set(Tag.all_objects.filter(
                account=account, id__in=mtm_ids
            ).values_list('id', flat=True))

        if valid_ids != mtm_ids:
            raise ValidationError({'error': _('Invalid request')})

    def update_items_links(self, links_model, item_type, link_field_name, item_ids, mtm_ids, action):
        """
        Edit items responsibles or tags
        :param links_model: ItemResponsibleLink or ItemTagLink
        :param item_type: ItemType
        :param link_field_name: user_id or tag_id
        :param item_ids: list
        :param mtm_ids: list
        :param action: 'add', 'remove' or 'set'
        :return:
        """

        account = self.request.account
        self._validate_link_ids(item_type, link_field_name, item_ids, mtm_ids)
        for item_id in item_ids:
            if action == self.ACTION_ADD:
                links_model.objects.bulk_create([
                    links_model(**{
                        'account': account,
                        'item_type': item_type,
                        'item_id': item_id,
                        link_field_name: mtm_id,
                    }) for mtm_id in mtm_ids
                ], ignore_conflicts=True)
            elif action == self.ACTION_REMOVE:
                links_model.objects.filter(**{
                    'account': account,
                    'item_type': item_type,
                    'item_id': item_id,
                    '{}__in'.format(link_field_name): mtm_ids,
                }).delete()
            elif action == self.ACTION_SET:
                links_model.objects.filter(**{
                    'account': account,
                    'item_type': item_type,
                    'item_id': item_id,
                }).delete()
                links_model.objects.bulk_create([
                    links_model(**{
                        'account': account,
                        'item_type': item_type,
                        'item_id': item_id,
                        link_field_name: mtm_id,
                    }) for mtm_id in mtm_ids
                ])

    def update_items_responsibles(self, item_type, item_ids, mtm_ids, action):
        self.update_items_links(ItemResponsibleLink, item_type, self.RESPONSIBLE_FIELD_NAME, item_ids, mtm_ids, action)

    def update_items_tags(self, item_type, item_ids, mtm_ids, action):
        self.update_items_links(ItemTagLink, item_type, self.TAG_FIELD_NAME, item_ids, mtm_ids, action)


class CompletedIntroRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not 'intro' in request.get_full_path() and not request.account.intro.is_completed:
            return redirect(reverse('intro'))

        return super().dispatch(request, *args, **kwargs)
