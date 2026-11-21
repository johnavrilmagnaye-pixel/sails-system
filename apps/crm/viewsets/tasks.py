import datetime as dt

from django.db.models import Q
from django.utils import timezone as tz
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from crm.filters import TaskFilterSet
from crm.forms import TaskForm
from crm.forms.tasks import TaskChangeDateForm
from crm.mixins import EditMTMFieldsMixin
from crm.models import Activity, Task, Note, PeriodicTask, ItemResponsibleLink
from crm.const import ItemType
from crm.tasks import notify_responsibles, set_remind_task_links, notifications_task_added
from crm.viewsets.base import ItemViewSet
from notifications.helpers import NotificationsHelper
from notifications.models import Notification


__all__ = (
    'TasksViewSet',
    'PeriodicTasksViewSet',
)


class TasksViewSet(ItemViewSet):
    model = Task
    filterset_class = TaskFilterSet
    ordering_fields = (
        'name', 'company__name', 'person__name', 'deal__name', 'state', 'expire_date', 'tags', 'details', 'user',
        'created_at',
    )
    search_fields = ('id', 'name', 'company__name', 'person__name', 'details',)

    def get_queryset(self):
        user = self.request.user

        tasks_qs = Task.objects.by_account(self.request.account).select_related(
            'company', 'person', 'deal', 'user'
        ).only(
            'id', 'name',  'state', 'expire_date', 'details', 'created_at', 'completed_at',
            'company_id', 'company__name', 'company__phones', 'company__emails',
            'person_id', 'person__name', 'person__post', 'person__phones', 'person__emails',
            'deal_id', 'deal__name',
            'user_id', 'user__email', 'user__first_name', 'user__last_name',
        )

        if not self.request.user_link.has_perm('view_all_task'):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(self.request.account).filter(
                item_type=ItemType.TASK.value,
                user_id=user.id
            ).values('item_id')
            tasks_qs = tasks_qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        return tasks_qs

    @action(detail=False, methods=['post'])
    def add(self, request):
        account = request.account
        data = request.data

        form = TaskForm(data=data, account=account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        task = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.TASK.value, [task.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.TASK.value, [task.id], [tag.id for tag in tags], 'set')

        if task.expire_date and task.expire_date < tz.now() and not account.is_gta:
            task.state = Task.STATE_OVERDUE
            task.save(update_fields=['state'])

        if task.expire_date and task.get_responsible_links().exists():
            set_remind_task_links.delay(request.account.id, task.id)

        notify_responsibles.delay(request.account.id, ItemType.TASK.value, task.id, [], request.user_link.name)

        Activity.log_addition(task)

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.TASK.value, [task.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.TASK.value, [task.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.TASK.value, [task.id]),
            'is_retrieve': True,
        }

        return Response({
            'task': task.serialize(**serialize_params),
            'calendar_task': task.calendar_serialize() if task.expire_date else None,
        })

    @action(detail=True, methods=['post'])
    def edit(self, request, pk):
        try:
            task = Task.objects.by_account(request.account).get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': _('This task does not exist')}, status=400)

        old_responsible_ids = task.get_responsible_ids()

        account = request.account
        data = request.data

        form = TaskForm(data=data, instance=task, account=account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        now = tz.now()
        if task.expire_date and not account.is_gta:
            if task.state == Task.STATE_PENDING and task.expire_date < now:
                task.state = Task.STATE_OVERDUE
            elif task.state == Task.STATE_OVERDUE and task.expire_date > now:
                task.state = Task.STATE_PENDING

        task = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.TASK.value, [task.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.TASK.value, [task.id], [tag.id for tag in tags], 'set')

        if 'expire_date' in form.changed_data or 'responsibles' in form.changed_data:
            set_remind_task_links.delay(request.account.id, task.id)

        notify_responsibles.delay(
            request.account.id,
            ItemType.TASK.value,
            task.id,
            old_responsible_ids,
            request.user_link.name
        )

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.TASK.value, [task.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.TASK.value, [task.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.TASK.value, [task.id]),
            'is_retrieve': True,
        }

        return Response({
            'task': task.serialize(**serialize_params),
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk):
        try:
            task = Task.objects.by_account(request.account).get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': _('This task does not exist')}, status=400)

        now = tz.now()

        task.state = Task.STATE_COMPLETED
        task.completed_at = now
        task.updated_at = now
        task.save(update_fields=('state', 'completed_at', 'updated_at'))

        Notification.objects.by_account(request.account).filter(
            user__in=task.get_responsible_ids(),
            text=mark_safe(
                _('Task reminder: <a href="{}">{}</a>').format(task.get_full_url(request.account), task.name)
            )
        ).update(is_read=True)
        if request.user != task.user:
            NotificationsHelper.crm.task_completed(request.account, task, request.user)

        note = Note.objects.create(
            account=request.account,
            text=_('Task completed'),
            user=request.user,
            item=task
        )

        return Response({
            'note': note.serialize(),
            'task': task.serialize(request),
        })

    @action(detail=True, methods=['post'])
    def undone(self, request, pk):
        try:
            task = Task.objects.by_account(request.account).get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': _('This task does not exist')}, status=400)

        now = tz.now()

        if task.expire_date and task.expire_date + dt.timedelta(hours=12) < now:
            if request.account.is_gta:
                task.state = Task.STATE_PENDING
            else:
                task.state = Task.STATE_OVERDUE
        else:
            task.state = Task.STATE_PENDING

        task.completed_at = None
        task.updated_at = now
        task.save(update_fields=('state', 'completed_at', 'updated_at'))

        note = Note.objects.create(
            account=request.account,
            text=_('Task reopened'),
            user=request.user,
            item=task
        )

        return Response({
            'success': True,
            'note': note.serialize(),
            'task': task.serialize(request),
        })

    @action(detail=True, methods=['post'])
    def change_date(self, request, pk):
        try:
            task = Task.objects.by_account(request.account).get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': _('This task does not exist')}, status=400)

        account = request.account
        data = request.data

        form = TaskChangeDateForm(data=data)
        if not form.is_valid():
            return Response({'error': _('Invalid date')}, status=400)

        # FIXME: use user timezone
        expire_date = form.cleaned_data['expire_date']
        if task.expire_date == expire_date:
            return Response({'error': _('The new date is the same as the current due date')}, status=400)

        task.expire_date = expire_date

        now = tz.now()
        if task.expire_date and not account.is_gta:
            if task.state == Task.STATE_PENDING and task.expire_date < now:
                task.state = Task.STATE_OVERDUE
            elif task.state == Task.STATE_OVERDUE and task.expire_date > now:
                task.state = Task.STATE_PENDING

        task.save(update_fields=['expire_date', 'state'])
        set_remind_task_links.delay(request.account.id, task.id)

        return Response({'state': task.state})


class PeriodicTasksViewSet(EditMTMFieldsMixin, GenericViewSet):
    model = PeriodicTask
    queryset = PeriodicTask.objects.none()

    def get_queryset(self):
        return PeriodicTask.objects.by_account(self.request.account)

    def list(self, request):
        periodic_tasks = self.get_queryset()
        data = [periodic_task.serialize() for periodic_task in self.paginate_queryset(periodic_tasks)]
        return self.get_paginated_response(data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        account = request.account
        data = request.data

        time = data.get('time')
        if not time:
            return Response({'error': _('Specify a time for the recurring task')}, status=400)

        form = TaskForm(data=data, account=account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        cleaned_data = form.cleaned_data

        periodic_task = PeriodicTask(
            account=request.account,
            company=cleaned_data.get('company'),
            person=cleaned_data.get('person'),
            deal=cleaned_data.get('deal'),
            name=cleaned_data.get('name'),
            details=cleaned_data.get('details'),
            user_id=request.user.id,
            time=time
        )

        periodic_task.period = int(data.get('period'))
        if periodic_task.period == PeriodicTask.PERIOD_WEEK:
            weekdays = list(map(int, data.get('weekdays', [])))
            if 0 in weekdays:
                periodic_task.weekdays = list(PeriodicTask.WEEKDAY_MAP.keys())
            else:
                periodic_task.weekdays = weekdays
        elif periodic_task.period == PeriodicTask.PERIOD_MONTH:
            months = list(map(int, data.get('months', [])))
            if 0 in months:
                periodic_task.months = list(PeriodicTask.MONTHS_MAP.keys())
            else:
                periodic_task.months = months
            periodic_task.monthdays = list(map(int, data.get('monthdays', [])))

        periodic_task.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.PERIODIC_TASK.value, [periodic_task.id],
            [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(
            ItemType.PERIODIC_TASK.value, [periodic_task.id], [tag.id for tag in tags], 'set'
        )

        # for key, value in cleaned_data.viewitems():
        #     if 'extra_field' in key:
        #         extra_field = ExtraField.objects.get(id=key.split('extra_field_')[1])
        #         periodic_task.set_extra_field_value(extra_field, value)

        return Response({
            'periodic_task': periodic_task.serialize(),
        })

    @action(detail=True, methods=['post'])
    def edit(self, request, pk):
        try:
            periodic_task = PeriodicTask.objects.by_account(request.account).get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': _('This recurring task does not exist')}, status=400)

        account = request.account
        data = request.data

        time = data.get('time')
        if not time:
            return Response({'error': _('Specify a time for the recurring task')}, status=400)

        form = TaskForm(data=data, account=account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        cleaned_data = form.cleaned_data

        periodic_task.company = cleaned_data.get('company')
        periodic_task.person = cleaned_data.get('person')
        periodic_task.deal = cleaned_data.get('deal')
        periodic_task.name = cleaned_data.get('name')
        periodic_task.details = cleaned_data.get('details')
        periodic_task.user_id = request.user.id
        periodic_task.time = time

        periodic_task.period = int(data.get('period'))
        if periodic_task.period == PeriodicTask.PERIOD_WEEK:
            weekdays = list(map(int, data.get('weekdays', [])))
            if 0 in weekdays:
                periodic_task.weekdays = list(PeriodicTask.WEEKDAY_MAP.keys())
            else:
                periodic_task.weekdays = weekdays
        elif periodic_task.period == PeriodicTask.PERIOD_MONTH:
            months = list(map(int, data.get('months', [])))
            if 0 in months:
                periodic_task.months = list(PeriodicTask.MONTHS_MAP.keys())
            else:
                periodic_task.months = months
            periodic_task.monthdays = list(map(int, data.get('monthdays', [])))

        periodic_task.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.PERIODIC_TASK.valuex, [periodic_task.id],
            [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(
            ItemType.PERIODIC_TASK.value, [periodic_task.id], [tag.id for tag in tags], 'set'
        )

        # for key, value in cleaned_data.viewitems():
        #     if 'extra_field' in key:
        #         extra_field = ExtraField.objects.get(id=key.split('extra_field_')[1])
        #         periodic_task.set_extra_field_value(extra_field, value)

        return Response({
            'periodic_task': periodic_task.serialize(),
        })

    @action(detail=True, methods=['POST'])
    def delete(self, request, *args, **kwargs):
        periodic_task = self.get_object()
        PeriodicTask.archive([periodic_task.id])
        return Response({})
