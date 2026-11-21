from django.contrib.auth.models import User

import django_filters

from crm.models import Activity

from .base import DateRangeFilter


__all__ = (
    'ActivityFilterSet',
)


class ActivityFilterSet(django_filters.FilterSet):
    user = django_filters.ModelChoiceFilter(queryset=User.objects.filter(is_active=True))
    created_at = DateRangeFilter()

    class Meta:
        model = Activity
        fields = ('user', 'created_at',)
