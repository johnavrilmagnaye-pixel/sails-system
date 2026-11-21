import datetime as dt

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel

from accounts.models import Account, UserAccountLink


class Notification(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)  # creator

    text = models.TextField(verbose_name=_('Notification text'))
    is_read = models.BooleanField(verbose_name=_('Read'), default=False)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return self.text

    def get_hide_url(self):
        return

    def serialize(self):
        return {
            'id': self.id,
            'text': self.text,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'hide_url': reverse('hide_notification', kwargs={'notification_id': self.id}),
        }


def notify_item_responsibles_default():
    return {
        'company': False,
        'person': False,
        'deal': False,
        'task': False
    }


class NotificationSettings(BaseModel):
    user_link = models.OneToOneField(
        UserAccountLink,
        related_name='notification_settings',
        on_delete=models.CASCADE,
    )

    remind_task = models.BooleanField(verbose_name=_('Email task reminders'), default=True)
    remind_task_before = models.DurationField(verbose_name=_('Remind before'), default=dt.timedelta(minutes=10))

    notify_item_responsibles = models.JSONField(
        verbose_name=_('Email notifications when assigned to'),
        default=notify_item_responsibles_default
    )
    notify_task_completed = models.BooleanField(
        verbose_name=_('Email notifications when a task is completed'), default=True
    )
    notify_company_note = models.BooleanField(default=False)
    notify_person_note = models.BooleanField(default=False)
    notify_deal_note = models.BooleanField(default=False)
    notify_task_note = models.BooleanField(default=False)

    def serialize(self):
        return {
            'remind_task': self.remind_task,
            'remind_task_before_hours': self.remind_task_before.seconds // 3600,
            'remind_task_before_minutes': (self.remind_task_before.seconds % 3600) // 60,
            'notify_task_completed': self.notify_task_completed,
            'notify_company_note': self.notify_company_note,
            'notify_person_note': self.notify_person_note,
            'notify_deal_note': self.notify_deal_note,
            'notify_task_note': self.notify_task_note,
            'notify_company_responsibles': self.notify_item_responsibles['company'],
            'notify_person_responsibles': self.notify_item_responsibles['person'],
            'notify_deal_responsibles': self.notify_item_responsibles['deal'],
            'notify_task_responsibles': self.notify_item_responsibles['task'],
        }
