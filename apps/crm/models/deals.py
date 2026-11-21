from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from positions import PositionField, PositionManager
from positions.managers import PositionQuerySet

from core.models import BaseModel
from core.utils import decimal_money

from accounts.models import Account, get_user_account_name
from crm.const import ItemType

from .base import BaseItem
from .contacts import Company, Person
from .links import ItemResponsibleLink, ItemExtraFieldLink


__all__ = (
    'get_verbose_budget',
    'DealStage',
    'DealStageChange',
    'DealCurrency',
    'Deal',
)


def get_verbose_budget(budget, currency):
    budget = decimal_money(budget)

    if currency.format:
        return currency.format.format(budget)

    return '{} {}'.format(budget, currency.code)


class PatchedPositionQuerySet(PositionQuerySet):
    def by_account(self, account):
        return self.filter(account=account)

    def reposition(self, save=True):
        position_field = self.model._meta.get_field('position')
        post_save.disconnect(position_field.update_on_save, sender=self.model)
        position = 0
        for obj in self:
            setattr(obj, self.position_field_name, position)
            if save:
                obj.save()
            position += 1
        post_save.connect(position_field.update_on_save, sender=self.model)
        return self


class PatchedPositionManager(PositionManager):
    def get_queryset(self):
        return PatchedPositionQuerySet(self.model, position_field_name=self.position_field_name)

    def by_account(self, account):
        return self.get_queryset().by_account(account)


class DealStage(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    position = PositionField()
    probability = models.PositiveSmallIntegerField(null=True, blank=True)

    objects = PatchedPositionManager()

    class Meta:
        ordering = ('position',)
        constraints = [
            models.UniqueConstraint(fields=('account', 'name'), name='unique_deal_stage_name_per_account'),
        ]

    def __str__(self):
        return self.name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'text': self.name,  # for select2 options
            'position': self.position,
        }


class DealCurrency(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    name = models.CharField(max_length=200, null=True)
    code = models.CharField(max_length=3, null=True)
    format = models.CharField(max_length=200, null=True)
    is_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'text': self.name,  # for select2 options
            'code': self.code,
            'format': self.format,
            'is_enabled': self.is_enabled,
        }


class Deal(BaseItem):
    CONTENT_TYPE = 3
    ITEM_TYPE = ItemType.DEAL.value

    GENITIVE = pgettext_lazy('grammatical genitive', 'deal')
    DATIVE = pgettext_lazy('grammatical dative', 'deal')
    ACCUSATIVE = pgettext_lazy('grammatical accusative', 'deal')

    PENDING = 1
    COMPLETED = 2
    FAILED = 3

    STATUS_CHOICES = (
        (PENDING, _('In progress')),
        (COMPLETED, _('Successfully completed')),
        (FAILED, _('Not completed')),
    )

    company = models.ForeignKey(Company, verbose_name=_('Company'), null=True, blank=True, on_delete=models.SET_NULL)
    person = models.ForeignKey(Person, verbose_name=_('Person'), null=True, blank=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    budget = models.DecimalField(max_digits=30, verbose_name=_('Budget'), decimal_places=2, null=True, blank=True, default=0)
    currency = models.ForeignKey(DealCurrency, verbose_name=_('Currency'), null=True, blank=True, on_delete=models.SET_NULL)
    status = models.SmallIntegerField(default=PENDING, choices=STATUS_CHOICES, verbose_name=_('Status'))
    stage = models.ForeignKey(DealStage, verbose_name=_('Stage'), null=True, blank=True, on_delete=models.SET_NULL)
    details = models.TextField(blank=True, verbose_name=_('Deal description'))

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Deal')
        verbose_name_plural = _('Deals')
        permissions = (
            ('view_all_deal', 'Can view all deals'),
            ('change_own_deal', 'Can change own deals'),
            ('change_assigned_deal', 'Can change assigned deals'),
            ('change_all_deal', 'Can change all deals'),
            ('delete_own_deal', 'Can delete own deals'),
        )

    def __str__(self):
        return self.name

    @classmethod
    def archive(cls, ids):
        from crm.models.misc import Activity, Note, Upload

        Activity.archive(model_name='deal', item_ids=ids)
        Note.archive(model_name='deal', item_ids=ids)
        Upload.archive(model_name='deal', item_ids=ids)

        cls.objects.filter(id__in=ids).update(
            is_archived=True,
            archived_at=tz.now()
        )

    @property
    def verbose_budget(self):
        if not self.currency:
            return decimal_money(self.budget)

        return get_verbose_budget(self.budget, self.currency)

    def serialize(self, *args, **kwargs):
        data = super().serialize(*args, **kwargs)

        responsible_links_map = kwargs.get('responsible_links_map', {})
        responsible_links = responsible_links_map.get(self.id, [])
        tag_links_map = kwargs.get('tag_links_map', {})
        tag_links = tag_links_map.get(self.id, [])
        extra_field_links_map = kwargs.get('extra_field_links_map', {})
        extra_field_links = extra_field_links_map.get(self.id, [])

        data.update({
            'status': self.status,
            'status_verbose': self.get_status_display(),
            'stage': self.stage.serialize() if self.stage else None,
            'currency': self.currency.serialize(),
            'budget_verbose': self.verbose_budget,
            'company': {
                'id': self.company_id,
                'name': self.company.name,
                'url': self.company.get_absolute_url(urlconf='crm.urls'),
                'phones': self.company.phones or [],
                'emails': self.company.emails or [],
            } if self.company else None,
            'person': {
                'id': self.person_id,
                'name': self.person.name,
                'url': self.person.get_absolute_url(urlconf='crm.urls'),
                'post': self.person.post,
                'phones': self.person.phones or [],
                'emails': self.person.emails or [],
            } if self.person else None,
        })

        budget = str(self.budget)
        if '.' in budget:
            data['budget'] = budget.rstrip('0').rstrip('.')
        else:
            data['budget'] = budget

        info = _('<b>Budget</b>: {}').format(self.verbose_budget)
        if self.company or self.person:
            info += _('<br><b>Contact:</b> ')
            if self.person:
                info += self.person.name
                if self.company:
                    info += ' ({})'.format(self.company.name)
            else:
                info += self.company.name
        if tag_links:
            info += _(' <br><b>Tags:</b> {}').format(
                ', '.join([link.tag.name for link in tag_links])
            )
        if responsible_links:
            info += _('<br><b>Assignees:</b> {}').format(', '.join([
                get_user_account_name(responsible_link.account, responsible_link.user)
                for responsible_link in responsible_links if responsible_link.user.is_active
            ]))
        if self.details:
            info += _('<br><b>Description:</b> {}').format(self.details)
        data['info'] = info

        extra_fields = {}
        for link in extra_field_links:
            extra_fields['extra_field_{}'.format(link.field_id)] = link.get_value()
        data['extra_fields'] = extra_fields

        return data

    def set_extra_field_value(self, extra_field, value):
        if not value:
            return

        link = ItemExtraFieldLink.objects.get_or_create(
            account=self.account,
            item_type=ItemType.DEAL.value,
            item_id=self.id,
            field=extra_field
        )[0]
        link.set_value(value)

    def get_extra_field_value(self, extra_field):
        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.DEAL.value,
                item_id=self.id,
                field=extra_field
            )
        except ItemExtraFieldLink.DoesNotExist:
            return ''

        return link.get_value()

    def is_user_responsible(self, user_id):
        return ItemResponsibleLink.objects.by_account(self.account).filter(
            item_type=ItemType.DEAL.value,
            item_id=self.id,
            user_id=user_id
        ).exists()


class DealStageChange(BaseModel):
    COMPLETE_STAGE = 1
    FAIL_STAGE = 2

    TYPE_CHOICES = (
        (COMPLETE_STAGE, 'complete_stage'),
        (FAIL_STAGE, 'fail_stage'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # creator
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)

    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)
    previous_stage = models.ForeignKey(DealStage, related_name='+', on_delete=models.CASCADE)
    new_stage = models.ForeignKey(DealStage, related_name='+', null=True, blank=True, on_delete=models.CASCADE)
    is_finish_change = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)
