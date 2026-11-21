import datetime as dt
import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone as tz
from django.utils.translation import gettext as _, gettext_lazy, pgettext_lazy

from core.models import BaseModel

from accounts.models import Account, get_user_account_name
from crm.const import ItemType

from .base import BaseItem
from .contacts import Company, Person
from .deals import Deal
from .links import ItemResponsibleLink, ItemTagLink, ItemExtraFieldLink
from .misc import Activity, Note, Upload


__all__ = (
    'PeriodicTask',
    'Task',
    'RemindTaskLink',
)


class PeriodicTask(BaseModel):
    ITEM_TYPE = ItemType.PERIODIC_TASK.value

    PERIOD_WEEK = 3
    PERIOD_MONTH = 4

    PERIOD_CHOICES = (
        (PERIOD_WEEK, gettext_lazy('Every week')),
        (PERIOD_MONTH, gettext_lazy('By month')),
    )

    WEEKDAY_MAP = {
        1: pgettext_lazy('recurring task weekday', 'Monday'),
        2: pgettext_lazy('recurring task weekday', 'Tuesday'),
        3: pgettext_lazy('recurring task weekday', 'Wednesday'),
        4: pgettext_lazy('recurring task weekday', 'Thursday'),
        5: pgettext_lazy('recurring task weekday', 'Friday'),
        6: pgettext_lazy('recurring task weekday', 'Saturday'),
        7: pgettext_lazy('recurring task weekday', 'Sunday'),
    }

    MONTHS_MAP = {
        1: gettext_lazy('January'),
        2: gettext_lazy('February'),
        3: gettext_lazy('March'),
        4: gettext_lazy('April'),
        5: gettext_lazy('May'),
        6: gettext_lazy('June'),
        7: gettext_lazy('July'),
        8: gettext_lazy('August'),
        9: gettext_lazy('September'),
        10: gettext_lazy('October'),
        11: gettext_lazy('November'),
        12: gettext_lazy('December'),
    }

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # creator

    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL)
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL)
    deal = models.ForeignKey(Deal, null=True, blank=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    time = models.TimeField()
    period = models.PositiveSmallIntegerField(choices=PERIOD_CHOICES)
    weekdays = models.JSONField(default=list)  # List of integers 1 - 7
    monthdays = models.JSONField(default=list)  # List of integers 1 - 31
    months = models.JSONField(default=list)  # List of integers 1 – 12

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.name

    @classmethod
    def archive(cls, ids):
        cls.objects.filter(id__in=ids).update(
            is_archived=True,
            archived_at=tz.now()
        )

    def serialize(self):
        # TODO: fix multiple queries for responsibles, tags, extra fields

        data = {
            'id': self.id,
            'name': self.name,
            'user': {
                'id': self.user_id,
                'name': get_user_account_name(self.account, self.user),
            },
            'user_id': self.user_id,
            'details': self.details,
            'time': self.time,
            'period': self.period,
            'weekdays': self.weekdays,
            'months': self.months,
            'monthdays': self.monthdays,

            'responsibles': [{
                'id': link.user.id,
                'name': get_user_account_name(link.account, link.user),
            } for link in self.get_responsible_links()],
            'tags': [{
                'id': link.tag.id,
                'name': link.tag.name,
            } for link in self.get_tag_links()],

            'company': {
                'id': self.company_id,
                'name': self.company.name,
                'url': self.company.get_absolute_url(urlconf='crm.urls'),
            } if self.company else None,
            'person': {
                'id': self.person_id,
                'name': self.person.name,
                'url': self.person.get_absolute_url(urlconf='crm.urls'),
            } if self.person else None,
            'deal': {
                'id': self.deal_id,
                'name': self.deal.name,
                'url': self.deal.get_absolute_url(urlconf='crm.urls'),
            } if self.deal else None,
        }

        if self.period == PeriodicTask.PERIOD_MONTH:
            data['verbose_period'] = _('{} on day {}').format(
                _('Every month') if len(self.months) == 12 else _('In selected months'),
                ', '.join(map(str, self.monthdays))
            )
        elif self.period == PeriodicTask.PERIOD_WEEK:
            if len(self.weekdays) == 7:
                data['verbose_period'] = _('Every day')
            else:
                data['verbose_period'] = _('Every week on {}').format(
                    ', '.join([self.WEEKDAY_MAP[weekday] for weekday in self.weekdays])
                )

        extra_fields = {}
        for link in ItemExtraFieldLink.objects.select_related('field').filter(
            item_type=ItemType.PERIODIC_TASK.value,
            item_id=self.id
        ):
            extra_fields['extra_field_{}'.format(link.field_id)] = link.get_value()
        data['extra_fields'] = extra_fields

        return data

    def create_task(self, account, next_date):
        expire_date = pytz.timezone(settings.TIME_ZONE).localize(dt.datetime.combine(next_date, self.time))
        if expire_date < tz.now():
            return

        task = Task.objects.create(
            account=account,
            company=self.company,
            person=self.person,
            deal=self.deal,
            name=self.name,
            details=self.details,
            expire_date=expire_date,
            user=self.user,
            periodic_task=self
        )

        if self.get_tag_links().exists():
            ItemTagLink.objects.bulk_create([
                ItemTagLink(
                    account=account,
                    item_type=ItemType.TASK.value,
                    item_id=task.id,
                    tag_id=link.tag_id
                ) for link in self.get_tag_links()
            ])

        has_responsibles = self.get_responsible_links().exists()
        if has_responsibles:
            ItemResponsibleLink.objects.bulk_create([
                ItemResponsibleLink(
                    account=account,
                    item_type=ItemType.TASK.value,
                    item_id=task.id,
                    user_id=link.user_id
                ) for link in self.get_responsible_links()
            ])

        if has_responsibles:
            from crm.tasks.base import set_remind_task_links
            set_remind_task_links.delay(account.id, task.id)

        Activity.log_addition(task)

    def get_responsible_links(self):
        return ItemResponsibleLink.objects.select_related('user').filter(
            item_type=ItemType.PERIODIC_TASK.value,
            item_id=self.id
        )

    def get_tag_links(self):
        return ItemTagLink.objects.by_account(self.account).select_related('tag').filter(
            item_type=ItemType.PERIODIC_TASK.value,
            item_id=self.id
        )

    def set_extra_field_value(self, extra_field, value):
        if not value:
            return

        link = ItemExtraFieldLink.objects.get_or_create(
            account=self.account,
            item_type=ItemType.PERIODIC_TASK.value,
            item_id=self.id,
            field=extra_field
        )[0]
        link.set_value(value)

    def get_extra_field_value(self, extra_field):
        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.PERIODIC_TASK.value,
                item_id=self.id,
                field=extra_field
            )
        except ItemExtraFieldLink.DoesNotExist:
            return ''

        return link.get_value()


class Task(BaseItem):
    CONTENT_TYPE = 4
    ITEM_TYPE = ItemType.TASK.value

    GENITIVE = pgettext_lazy('grammatical genitive', 'task')
    DATIVE = pgettext_lazy('grammatical dative', 'task')
    ACCUSATIVE = pgettext_lazy('grammatical accusative', 'task')

    STATE_PENDING = 1
    STATE_COMPLETED = 2
    STATE_OVERDUE = 3

    STATE_CHOICES = (
        (STATE_PENDING, gettext_lazy('Pending')),
        (STATE_COMPLETED, gettext_lazy('Completed')),
        (STATE_OVERDUE, gettext_lazy('Overdue')),
    )

    company = models.ForeignKey(Company, verbose_name=gettext_lazy('Company'), null=True, blank=True, on_delete=models.SET_NULL)
    person = models.ForeignKey(Person, verbose_name=gettext_lazy('Person'), null=True, blank=True, on_delete=models.SET_NULL)
    deal = models.ForeignKey(Deal, verbose_name=gettext_lazy('Deal'), null=True, blank=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=200, verbose_name=gettext_lazy('Name'))
    details = models.TextField(blank=True, verbose_name=gettext_lazy('Task description'))

    expire_date = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Due date'))
    completed_at = models.DateTimeField(null=True, blank=True)

    state = models.PositiveSmallIntegerField(choices=STATE_CHOICES, default=STATE_PENDING, null=True, blank=True)

    periodic_task = models.ForeignKey(PeriodicTask, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = gettext_lazy('Task')
        verbose_name_plural = gettext_lazy('Tasks')
        permissions = (
            ('view_all_task', 'Can view all tasks'),
            ('change_own_task', 'Can change own tasks'),
            ('change_assigned_task', 'Can change assigned tasks'),
            ('delete_own_task', 'Can delete own tasks'),
        )

    def __str__(self):
        return self.name

    @property
    def numbered_name(self):
        return f'#{self.id} {self.name}'

    @classmethod
    def archive(cls, ids):
        Activity.archive(model_name='task', item_ids=ids)
        Note.archive(model_name='task', item_ids=ids)
        Upload.archive(model_name='task', item_ids=ids)

        cls.objects.filter(id__in=ids).update(
            is_archived=True,
            archived_at=tz.now()
        )

    def get_verbose_state(self, timezone=None):
        if not self.expire_date or not timezone:
            return _('Scheduled')

        if self.state in (self.STATE_COMPLETED, self.STATE_OVERDUE):
            return self.get_state_display()

        now = tz.now().astimezone(timezone)
        expire_date = self.expire_date.astimezone(timezone)

        if now.year == expire_date.year and now.month == expire_date.month and now.day == expire_date.day:
            return _('Today')

        tomorrow = now + dt.timedelta(days=1)
        if tomorrow.year == expire_date.year and tomorrow.month == expire_date.month and tomorrow.day == expire_date.day:
            return _('Tomorrow')

        if now.year == expire_date.year:
            if now.isocalendar()[1] == expire_date.isocalendar()[1]:
                return _('This week')
            elif now.isocalendar()[1] + 1 == expire_date.isocalendar()[1]:
                return _('Next week')

            if now.month == expire_date.month:
                return _('This month')
            elif now.month + 1 == expire_date.month:
                return _('Next month')

        return _('Scheduled')

    def calendar_serialize(self):
        return {
            'task_id': self.id,
            'title': self.numbered_name,
            'start': self.expire_date.isoformat() if self.expire_date else None,
            'url': self.get_absolute_url(urlconf='crm.urls'),
            'color': '#d9534f' if self.state == self.STATE_OVERDUE else '#428bca',
        }

    def serialize(self, request=None, is_retrieve=False, *args, **kwargs):
        data = super().serialize(*args, **kwargs)

        extra_field_links_map = kwargs.get('extra_field_links_map', {})
        extra_field_links = extra_field_links_map.get(self.id, [])

        data.update({
            'state': self.state,
            'expire_date': self.expire_date.isoformat() if self.expire_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,

            'person': {
                'id': self.person_id,
                'name': self.person.name,
                'url': self.person.get_absolute_url(urlconf='crm.urls'),
                'post': self.person.post,
                'phones': self.person.phones or [],
                'emails': self.person.emails or [],
            } if self.person else None,
            'deal': {
                'id': self.deal_id,
                'name': self.deal.name,
                'url': self.deal.get_absolute_url(urlconf='crm.urls'),
            } if self.deal else None,
        })

        # TODO: for what? and pass company links in serialize
        if is_retrieve:
            data['company'] = self.company.serialize() if self.company else None
        else:
            data['company'] = {
                'id': self.company_id,
                'name': self.company.name,
                'url': self.company.get_absolute_url(urlconf='crm.urls'),
                'phones': self.company.phones or [],
                'emails': self.company.emails or [],
            } if self.company else None

        if request.account.is_gta:
            if self.state == Task.STATE_COMPLETED:
                data['verbose_state'] = _('Completed')
            else:
                data['verbose_state'] = _('Not completed')
        else:
            data['verbose_state'] = self.get_verbose_state(request.user_link.timezone)

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
            item_type=ItemType.TASK.value,
            item_id=self.id,
            field=extra_field
        )[0]
        link.set_value(value)

    def get_extra_field_value(self, extra_field):
        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.TASK.value,
                item_id=self.id,
                field=extra_field
            )
        except ItemExtraFieldLink.DoesNotExist:
            return ''

        return link.get_value()

    def is_user_responsible(self, user_id):
        return ItemResponsibleLink.objects.by_account(self.account).filter(
            item_type=ItemType.TASK.value,
            item_id=self.id,
            user_id=user_id
        ).exists()


class RemindTaskLink(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    responsible = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True)
    is_reminded = models.BooleanField(default=False)

    class Meta:
        unique_together = ('task', 'responsible')

    def __str__(self):
        return '{0} - {1}'.format(self.task_id, self.responsible_id)
