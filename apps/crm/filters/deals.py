from django.contrib.auth.models import User

import django_filters

from crm.models import Company, Person, Deal, DealCurrency, DealStage, ItemExtraFieldLink, ItemType

from .base import NumberRangeFilter, DateRangeFilter, BaseItemFilerSet, ResponsiblesFilter, TagsFilter


__all__ = (
    'DealFilterSet',
    'FunnelFilterSet',
)


class DealStatusFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value is not None:
            if value == '1':
                return qs.filter(status=Deal.PENDING)
            elif value == '2':
                return qs.exclude(status=Deal.PENDING)
        return qs


class DealFilterSet(BaseItemFilerSet):
    model_name = ItemType.DEAL.value
    extra_field_links_queryset = ItemExtraFieldLink.objects.filter(item_type=ItemType.DEAL.value)

    company = django_filters.ModelChoiceFilter(queryset=Company.objects.all())
    person = django_filters.ModelChoiceFilter(queryset=Person.objects.all())
    budget = NumberRangeFilter()
    currency = django_filters.ModelChoiceFilter(queryset=DealCurrency.objects.filter(is_enabled=True))
    status = DealStatusFilter()
    stage = django_filters.ModelChoiceFilter(queryset=DealStage.objects.all())
    responsibles = ResponsiblesFilter()
    tags = TagsFilter()
    user = django_filters.ModelChoiceFilter(queryset=User.objects.filter(is_active=True))
    created_at = DateRangeFilter()

    class Meta:
        model = Deal
        fields = (
            'budget', 'currency', 'status', 'stage', 'tags', 'responsibles', 'user', 'created_at', 'company', 'person',
        )


class FunnelFilterSet(BaseItemFilerSet):
    model_name = ItemType.DEAL.value
    extra_field_links_queryset = ItemExtraFieldLink.objects.filter(item_type=ItemType.DEAL.value)

    budget = NumberRangeFilter()
    currency = django_filters.ModelChoiceFilter(queryset=DealCurrency.objects.filter(is_enabled=True))
    responsibles = ResponsiblesFilter()
    tags = TagsFilter()
    user = django_filters.ModelChoiceFilter(queryset=User.objects.filter(is_active=True))
    created_at = DateRangeFilter()

    class Meta:
        model = Deal
        fields = ('budget', 'currency', 'tags', 'responsibles', 'user', 'created_at',)
