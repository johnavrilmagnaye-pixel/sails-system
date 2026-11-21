from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import Account, UserAccountLink
from core.models import ByAccountManager
from crm.helpers import ItemsHelper

from crm.const import ITEM_TYPE_CHOICES

from .misc import Tag, ExtraField


__all__ = (
    'ItemResponsibleLink',
    'ItemTagLink',
    'ItemExtraFieldLink',
)


class AccountItemLinkMixin:
    """ Validate both ends of a denormalized item link """

    def clean(self):
        super().clean()
        item_model = ItemsHelper.get_model(self.item_type)
        invalid_item = self.account_id and self.item_id and (
            item_model is None
            or not item_model.all_objects.filter(pk=self.item_id, account_id=self.account_id).exists()
        )
        if invalid_item or self._has_invalid_related_account():
            raise ValidationError(_('Invalid request'))

    def _has_invalid_related_account(self):
        return False

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ItemResponsibleLink(AccountItemLinkMixin, models.Model):
    """ Link between CRM item and its responsible """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=32, choices=ITEM_TYPE_CHOICES)
    item_id = models.PositiveIntegerField(db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)

    objects = ByAccountManager()

    class Meta:
        unique_together = (
            ('item_type', 'item_id', 'user'),
        )

    def _has_invalid_related_account(self):
        if self.account_id and self.user_id:
            return not UserAccountLink.objects.filter(
                account_id=self.account_id,
                user_id=self.user_id,
                is_active=True,
                user__is_active=True,
            ).exists()
        return False


class ItemTagLink(AccountItemLinkMixin, models.Model):
    """ Link between CRM item and its tag """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=32, choices=ITEM_TYPE_CHOICES)
    item_id = models.PositiveIntegerField(db_index=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, db_index=True)
    objects = ByAccountManager()

    class Meta:
        unique_together = (
            ('item_type', 'item_id', 'tag'),
        )

    def _has_invalid_related_account(self):
        return self.account_id and self.tag_id and not Tag.all_objects.filter(
            pk=self.tag_id, account_id=self.account_id
        ).exists()


class ItemExtraFieldLink(AccountItemLinkMixin, models.Model):
    """ Link between CRM item and its extra field """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=32, choices=ITEM_TYPE_CHOICES)
    item_id = models.PositiveIntegerField(db_index=True)
    field = models.ForeignKey(ExtraField, on_delete=models.CASCADE)

    value = models.CharField(max_length=1000, blank=True)
    dt_value = models.DateTimeField(null=True, blank=True)
    boolean_value = models.BooleanField(null=True)
    number_value = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    json_value = models.JSONField(null=True, blank=True)
    objects = ByAccountManager()

    class Meta:
        unique_together = (
            ('item_type', 'item_id', 'field'),
        )

    def _has_invalid_related_account(self):
        if not self.account_id or not self.field_id:
            return False

        expected_model = ItemsHelper.ITEM_MODEL_NAMES.get(self.item_type)
        return not ExtraField.all_objects.filter(
            pk=self.field_id,
            account_id=self.account_id,
            content_type__model=expected_model.lower() if expected_model else '',
        ).exists()

    def get_value(self):
        if self.field.is_dt:
            return self.dt_value
        elif self.field.is_number:
            return self.number_value
        elif self.field.is_json:
            return self.json_value

        return self.value

    def set_value(self, value):
        update_fields = []

        if self.field.is_dt:
            self.dt_value = value
            update_fields.append('dt_value')
        elif self.field.is_number:
            self.number_value = value
            update_fields.append('number_value')
        elif self.field.is_json:
            self.json_value = value
            update_fields.append('json_value')
        else:
            self.value = value
            update_fields.append('value')

        self.save(update_fields=update_fields)
