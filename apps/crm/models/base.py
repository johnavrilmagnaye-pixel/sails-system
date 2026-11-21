from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from django.db import models

from core.models import BaseModel

from accounts.models import Account, get_user_account_name

from .misc import Note, Upload, ExtraField


class BaseItem(BaseModel):
    """ Base Model for companies, persons, deals and tasks """
    CONTENT_TYPE = None
    ITEM_TYPE = None
    GENITIVE = None
    DATIVE = None
    ACCUSATIVE = None

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # creator

    name = models.CharField(max_length=200)
    details = models.TextField(blank=True)

    notes = GenericRelation(Note, object_id_field='item_id')
    uploads = GenericRelation(Upload, object_id_field='item_id')

    class Meta:
        abstract = True
        ordering = ('-created_at',)

    def get_absolute_url(self, urlconf=None):
        return reverse(self.ITEM_TYPE, urlconf=urlconf, kwargs={'{}_id'.format(self.ITEM_TYPE): self.id})

    def get_full_url(self, account, urlconf=None):
        return '{}://{}.{}{}'.format(settings.DEFAULT_PROTOCOL, account.name, settings.DEFAULT_DOMAIN,
                                     self.get_absolute_url(urlconf))

    def get_extra_fields(self):
        return ExtraField.objects.by_account(self.account).filter(content_type=ContentType.objects.get_for_model(self))

    def set_extra_field_value(self, extra_field, value):
        raise NotImplementedError

    def get_extra_field_value(self, extra_field):
        raise NotImplementedError

    def get_content_type(self):
        return ContentType.objects.get(model=self._meta.model_name)

    def serialize(self, *args, **kwargs):
        responsible_links_map = kwargs.get('responsible_links_map', {})
        responsible_links = responsible_links_map.get(self.id, [])

        tag_links_map = kwargs.get('tag_links_map', {})
        tag_links = tag_links_map.get(self.id, [])

        data = {
            'id': self.id,
            'name': self.name,
            'details': self.details,
            'user': {
                'id': self.user_id,
                'name': get_user_account_name(self.account, self.user),
            },
            'user_id': self.user_id,
            'url': self.get_absolute_url(urlconf='crm.urls'),
            'created_at': self.created_at.isoformat(),

            'responsibles': [{
                'id': link.user.id,
                'name': get_user_account_name(link.account, link.user),
            } for link in responsible_links],
            'tags': [{
                'id': link.tag.name,
                'name': link.tag.name,
            } for link in tag_links],

            'checked': False,  # for grids, TODO: remove after new front release
        }

        return data

    def option_serialize(self):
        return {
            'id': self.id,
            'text': self.name,
        }

    def notify_responsibles(self):
        raise NotImplementedError

    def get_responsible_links(self, is_active=None):
        # TODO: get rid of local imports
        from .links import ItemResponsibleLink

        qs = ItemResponsibleLink.objects.by_account(self.account).select_related('user').filter(
            item_type=self.ITEM_TYPE,
            item_id=self.id
        )

        if is_active is not None:
            return qs.filter(user__is_active=True)

        return qs

    def get_responsible_ids(self):
        return list(self.get_responsible_links().values_list('user_id', flat=True))

    def get_tag_links(self):
        # TODO: get rid of local imports
        from .links import ItemTagLink

        return ItemTagLink.objects.by_account(self.account).select_related('tag').filter(
            item_type=self.ITEM_TYPE,
            item_id=self.id,
        )
