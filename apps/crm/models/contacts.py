from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from core.models import BaseModel

from accounts.models import Account
from crm.const import ItemType

from .base import BaseItem
from .links import ItemExtraFieldLink


__all__ = (
    'ContactsImport',
    'Company',
    'Person',
)


class ContactsImport(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='contacts_imports', on_delete=models.DO_NOTHING)  # creator

    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='imports', max_length=1000)
    fields_map = models.JSONField(null=True, blank=True)
    rows_cnt = models.PositiveIntegerField(null=True, blank=True)
    duplicates_cnt = models.PositiveIntegerField(null=True, blank=True)

    companies_cnt = models.PositiveIntegerField()
    persons_cnt = models.PositiveIntegerField()

    merge_contacts = models.BooleanField(null=True)
    company_merge_field = models.CharField(max_length=30, blank=True)
    person_merge_field = models.CharField(max_length=30, blank=True)

    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)

    def archive(self):
        self.is_archived = True
        self.archived_at = tz.now()
        self.save(update_fields=('is_archived', 'archived_at'))

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'companies_cnt': self.companies_cnt,
            'persons_cnt': self.persons_cnt,
            'completed_at': self.completed_at.isoformat(),
        }


class Company(BaseItem):
    CONTENT_TYPE = 1
    ITEM_TYPE = ItemType.COMPANY.value

    GENITIVE = pgettext_lazy('grammatical genitive', 'company')
    DATIVE = pgettext_lazy('grammatical dative', 'company')
    ACCUSATIVE = pgettext_lazy('grammatical accusative', 'company')

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    details = models.TextField(blank=True, verbose_name=_('Additional information'))

    address = models.CharField(max_length=400, verbose_name=_('Address'), blank=True)
    website = models.URLField(null=True, blank=True, verbose_name=_('Website'))

    phones = models.JSONField(null=True, blank=True, verbose_name=_('Phone'))
    emails = models.JSONField(null=True, blank=True, verbose_name=_('Email address'))

    contacts_import = models.ForeignKey(ContactsImport, null=True, blank=True, related_name='companies', on_delete=models.SET_NULL)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
        permissions = (
            ('view_all_company', 'Can view all companies'),
            ('change_own_company', 'Can change own companies'),
            ('change_assigned_company', 'Can change assigned companies'),
            ('change_all_company', 'Can change all companies'),
            ('delete_own_company', 'Can delete own companies'),
        )

    def __str__(self):
        return self.name

    @classmethod
    def archive(cls, ids):
        from crm.models.misc import Activity, Note, Upload
        from crm.models.deals import Deal
        from crm.models.tasks import Task

        Activity.archive(model_name='company', item_ids=ids)
        Note.archive(model_name='company', item_ids=ids)
        Upload.archive(model_name='company', item_ids=ids)

        Task.archive(Task.objects.filter(company_id__in=ids).values_list('id', flat=True))
        Deal.archive(Deal.objects.filter(company_id__in=ids).values_list('id', flat=True))
        Person.archive(Person.objects.filter(company_id__in=ids).values_list('id', flat=True))

        cls.objects.filter(id__in=ids).update(
            is_archived=True,
            archived_at=tz.now()
        )

    def serialize(self, *args, **kwargs):
        data = super().serialize(*args, **kwargs)

        extra_field_links_map = kwargs.get('extra_field_links_map', {})
        extra_field_links = extra_field_links_map.get(self.id, [])

        data.update({
            'address': self.address,
            'website': self.website,
            'emails': self.emails or [],
            'phones': self.phones or [],
        })

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
            item_type=ItemType.COMPANY.value,
            item_id=self.id,
            field=extra_field
        )[0]
        link.set_value(value)

    def get_extra_field_value(self, extra_field):
        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.COMPANY.value,
                item_id=self.id,
                field=extra_field
            )
        except ItemExtraFieldLink.DoesNotExist:
            return ''

        return link.get_value()


class Person(BaseItem):
    CONTENT_TYPE = 2
    ITEM_TYPE = ItemType.PERSON.value

    GENITIVE = pgettext_lazy('grammatical genitive', 'contact')
    DATIVE = pgettext_lazy('grammatical dative', 'contact')
    ACCUSATIVE = pgettext_lazy('grammatical accusative', 'contact')

    name = models.CharField(max_length=200, verbose_name=_('Full name'))
    details = models.TextField(blank=True, verbose_name=_('Additional information'))

    company = models.ForeignKey(Company, verbose_name=_('Company'), null=True, blank=True, on_delete=models.SET_NULL)
    post = models.CharField(max_length=200, verbose_name=_('Job title'), blank=True)

    phones = models.JSONField(null=True, blank=True, verbose_name=_('Phone'))
    emails = models.JSONField(null=True, blank=True, verbose_name=_('Email address'))

    contacts_import = models.ForeignKey(ContactsImport, null=True, blank=True, related_name='persons', on_delete=models.SET_NULL)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')
        permissions = (
            ('view_all_person', 'Can view all persons'),
            ('change_own_person', 'Can change own persons'),
            ('change_assigned_person', 'Can change assigned persons'),
            ('change_all_person', 'Can change all persons'),
            ('delete_own_person', 'Can delete own persons'),
        )

    def __str__(self):
        return self.name

    @classmethod
    def archive(cls, ids):
        from crm.models.misc import Activity, Note, Upload
        from crm.models.deals import Deal
        from crm.models.tasks import Task

        Activity.archive(model_name='person', item_ids=ids)
        Note.archive(model_name='person', item_ids=ids)
        Upload.archive(model_name='person', item_ids=ids)

        Task.archive(Task.objects.filter(person_id__in=ids).values_list('id', flat=True))
        Deal.archive(Deal.objects.filter(person_id__in=ids).values_list('id', flat=True))

        cls.objects.filter(id__in=ids).update(
            is_archived=True,
            archived_at=tz.now()
        )

    def serialize(self, *args, **kwargs):
        data = super().serialize(*args, **kwargs)

        extra_field_links_map = kwargs.get('extra_field_links_map', {})
        extra_field_links = extra_field_links_map.get(self.id, [])

        data.update({
            'company': {
                'id': self.company_id,
                'name': self.company.name,
                'url': self.company.get_absolute_url(urlconf='crm.urls'),
            } if self.company else None,
            'post': self.post,
            'emails': self.emails or [],
            'phones': self.phones or [],
        })

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
            item_type=ItemType.PERSON.value,
            item_id=self.id,
            field=extra_field
        )[0]
        link.set_value(value)

    def get_extra_field_value(self, extra_field):
        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.PERSON.value,
                item_id=self.id,
                field=extra_field,
            )
        except ItemExtraFieldLink.DoesNotExist:
            return ''

        return link.get_value()
