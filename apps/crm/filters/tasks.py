from django.contrib.auth.models import User

import django_filters

from crm.models import Company, Person, Deal, Task, ItemExtraFieldLink, ItemType

from .base import DateRangeFilter, ResponsiblesFilter, TagsFilter, BaseItemFilerSet


__all__ = (
    'BaseTaskFilterSet',
    'TaskFilterSet',
)


class TaskStateFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value is not None:
            if value == '1':
                return qs.filter(state__in=[Task.STATE_PENDING, Task.STATE_OVERDUE])
            elif value == '2':
                return qs.filter(state=Task.STATE_COMPLETED)
            elif value == '3':
                return qs.filter(state=Task.STATE_OVERDUE)
        return qs


class BaseTaskFilterSet(BaseItemFilerSet):
    model_name = ItemType.TASK.value
    extra_field_links_queryset = ItemExtraFieldLink.objects.filter(item_type=ItemType.TASK.value)

    company = django_filters.ModelChoiceFilter(queryset=Company.objects.all())
    person = django_filters.ModelChoiceFilter(queryset=Person.objects.all())
    deal = django_filters.ModelChoiceFilter(queryset=Deal.objects.all())
    expire_date = DateRangeFilter()
    responsibles = ResponsiblesFilter()
    tags = TagsFilter()
    user = django_filters.ModelChoiceFilter(queryset=User.objects.filter(is_active=True))
    created_at = DateRangeFilter()
    state = TaskStateFilter()

    class Meta:
        model = Task
        fields = (
            'state', 'expire_date', 'tags', 'responsibles', 'user', 'created_at',
        )


class TaskFilterSet(BaseTaskFilterSet):
    class Meta:
        model = Task
        fields = (
            'state', 'expire_date', 'tags', 'responsibles', 'user', 'created_at', 'company', 'person', 'deal',
        )
