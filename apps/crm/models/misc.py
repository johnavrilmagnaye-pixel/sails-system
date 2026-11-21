import uuid

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.db import models
from django.dispatch import receiver
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel

from accounts.models import Account, get_user_account_name
from crm.const import ItemType


__all__ = (
    'Activity',
    'Tag',
    'Upload',
    'Note',
    'ExtraField',
    'ItemsExport',
    'get_upload_path',
)


class Tag(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def serialize(self, is_settings=None):
        if is_settings:
            from .contacts import Company, Person
            from .deals import Deal
            from .links import ItemTagLink
            from .tasks import Task

            base_qs = ItemTagLink.objects.by_account(self.account).filter(tag_id=self.id)
            companies_count = base_qs.filter(item_type=ItemType.COMPANY.value).exclude(
                item_id__in=Company.all_objects.filter(is_archived=True).values('id')
            ).count()
            persons_count = base_qs.filter(item_type=ItemType.PERSON.value).exclude(
                item_id__in=Person.all_objects.filter(is_archived=True).values('id')
            ).count()
            deals_count = base_qs.filter(item_type=ItemType.DEAL.value).exclude(
                item_id__in=Deal.all_objects.filter(is_archived=True).values('id')
            ).count()
            tasks_count = base_qs.filter(item_type=ItemType.TASK.value).exclude(
                item_id__in=Task.all_objects.filter(is_archived=True).values('id')
            ).count()

            return {
                'id': self.id,
                'name': self.name,
                'companies_cnt': companies_count,
                'persons_cnt': persons_count,
                'deals_cnt': deals_count,
                'tasks_cnt': tasks_count,
            }

        return {
            'id': self.name,
            'name': self.name,
            'text': self.name,  # for select2 options
        }


class Activity(BaseModel):
    """ Activity log for CRM items created by user """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # creator

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    item_id = models.PositiveIntegerField()
    item = GenericForeignKey(fk_field='item_id')

    updated_at = None  # do not need this field here

    class Meta:
        ordering = ('-created_at',)
        get_latest_by = 'created_at'

    @classmethod
    def archive(cls, model_name, item_ids):
        cls.objects.filter(
            content_type__model=model_name,
            item_id__in=item_ids,
            is_archived=False
        ).update(
            is_archived=True,
            archived_at=tz.now()
        )

    @classmethod
    def log_addition(cls, item):
        cls.objects.create(
            account=item.account,
            item=item,
            user=item.user
        )

    def serialize(self):
        item = {
            'item_id': self.item_id,
        }

        if self.content_type.model == 'note':
            item['text'] = self.item.text
        else:
            item['name'] = self.item.name
            item['url'] = self.item.get_download_url() if self.content_type.model == 'upload' else self.item.get_absolute_url(urlconf='crm.urls')

        if self.content_type.model in ('note', 'upload'):
            item['parent'] = {
                'content_type': self.item.content_type.model,
                'name': self.item.item.name,
                'url': self.item.item.get_absolute_url(),
            }

        return {
            'id': self.id,
            'user': get_user_account_name(self.account, self.user),
            'title': self.content_type.name,
            'content_type': self.content_type.model,
            'created_at': self.created_at.isoformat(),
            'item': item,
        }


class Note(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # creator

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    item_id = models.PositiveIntegerField()
    item = GenericForeignKey(fk_field='item_id')

    text = models.TextField()

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')
        permissions = (
            ('view_all_note', 'Can view all notes'),
            ('delete_own_note', 'Can delete own notes'),
        )

    def __str__(self):
        return self.text

    @classmethod
    def archive(cls, ids=None, model_name=None, item_ids=None):
        if ids:
            qs = cls.objects.filter(id__in=ids)
        else:
            qs = cls.objects.filter(
                content_type__model=model_name,
                item_id__in=item_ids
            )
            ids = qs.values_list('id', flat=True)

        Activity.archive('note', ids)
        qs.update(
            is_archived=True,
            archived_at=tz.now()
        )

    def get_absolute_url(self):
        from crm.models.contacts import Company, Person
        from crm.models.deals import Deal
        from crm.models.tasks import Task

        model = {
            Company.CONTENT_TYPE: 'company',
            Person.CONTENT_TYPE: 'person',
            Deal.CONTENT_TYPE: 'deal',
            Task.CONTENT_TYPE: 'task'
        }

        return '/{}/{}/'.format(model[self.content_type_id], self.item_id)

    def serialize(self):
        uploads = Upload.objects.by_account(self.account).filter(note_id=self.id)

        return {
            'id': self.id,
            'text': self.text,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id,
            'user': {
                'id': self.user.id,
                'name': get_user_account_name(self.account, self.user),
            },
            'uploads': [{
                'id': upload.id,
                'name': upload.name,
            } for upload in uploads]
        }


def get_upload_path(instance, filename):
    return 'uploads/{}'.format(uuid.uuid4())


class Upload(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # creator
    note = models.ForeignKey(Note, null=True, blank=True, on_delete=models.SET_NULL)

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    item_id = models.PositiveIntegerField()
    item = GenericForeignKey(fk_field='item_id')

    file = models.FileField(upload_to=get_upload_path)
    name = models.CharField(max_length=200, null=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('File')
        verbose_name_plural = _('Files')
        permissions = (
            ('view_all_upload', 'Can view all files'),
            ('delete_own_upload', 'Can delete own files'),
        )

    def __str__(self):
        return self.name

    @classmethod
    def archive(cls, ids=None, model_name=None, item_ids=None):
        if ids:
            qs = cls.objects.filter(id__in=ids)
        else:
            qs = cls.objects.filter(
                content_type__model=model_name,
                item_id__in=item_ids
            )
            ids = qs.values_list('id', flat=True)

        Activity.archive('upload', ids)
        qs.update(
            is_archived=True,
            archived_at=tz.now()
        )

    def get_download_url(self):
        return reverse('download_upload', kwargs={'upload_id': self.id})

    def get_absolute_url(self):
        return '/{}/{}/'.format(self.content_type.model, self.item_id)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id,
            'user': {
                'id': self.user.id,
                'name': get_user_account_name(self.account, self.user),
            },
        }


class ExtraField(BaseModel):
    TYPE_STRING = 1
    TYPE_TEXT = 2
    TYPE_SELECT = 3
    TYPE_DATE = 4
    TYPE_DATETIME = 5
    TYPE_NUMBER = 6
    TYPE_PHONES = 7
    TYPE_EMAILS = 8

    TYPE_CHOICES = (
        (TYPE_STRING, _('String')),
        (TYPE_TEXT, _('Text')),
        (TYPE_SELECT, _('List')),
        (TYPE_DATE, _('Date')),
        (TYPE_DATETIME, _('Date and time')),
        (TYPE_NUMBER, _('Number')),
        (TYPE_PHONES, _('Phone')),
        (TYPE_EMAILS, _('Email address')),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    # TODO: replace content_type with item_type

    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=TYPE_STRING)
    select_options = models.JSONField(null=True, blank=True)
    is_required = models.BooleanField(null=True)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.name

    def archive(self):
        self.is_archived = True
        self.archived_at = tz.now()
        self.save(update_fields=('is_archived', 'archived_at'))

    @property
    def is_dt(self):
        return self.type in (self.TYPE_DATE, self.TYPE_DATETIME)

    @property
    def is_number(self):
        return self.type == self.TYPE_NUMBER

    @property
    def is_json(self):
        return self.type in (self.TYPE_PHONES, self.TYPE_EMAILS)

    def serialize(self):
        options = self.select_options
        if options:
            options = [{'id': option, 'text': option} for option in options]

        return {
            'id': self.id,
            'name': self.name,
            'codename': 'extra_field_{}'.format(self.id),
            'type': self.type,
            'content_type': self.content_type.model,
            'select_options': self.select_options,
            'options': options,
            'is_required': bool(self.is_required),
            'type_label': self.get_type_display(),
        }


class ItemsExport(BaseModel):
    EXTENSION_CSV = 'csv'
    EXTENSION_XLS = 'xls'

    EXTENSION_CHOICES = (
        (EXTENSION_CSV, 'CSV'),
        (EXTENSION_XLS, 'XLS (Excel)'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # creator

    model_name = models.CharField(max_length=30)
    item_ids = models.JSONField()
    extension = models.CharField(max_length=10, choices=EXTENSION_CHOICES)
    result = models.FileField(upload_to='exports', null=True, blank=True)
    is_ready = models.BooleanField(default=False)


@receiver(models.signals.post_delete, sender=Upload)
def delete_file_from_disk(sender, instance, **kwargs):
    instance.file.storage.delete(instance.file.name)
