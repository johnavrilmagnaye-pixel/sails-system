from django.contrib.auth.models import User

import django_filters

from crm.models import Company, Person, Deal, Task, ItemExtraFieldLink, ItemType

from .base import DateRangeFilter, ResponsiblesFilter, TagsFilter, BaseItemFilerSet


__all__ = (
    'CompanyFilterSet',
    'PersonFilterSet',
)


class ContactsMiscFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value:
            account_ids = qs.values('account_id')
            field_name = 'company_id' if self.model == Company else 'person_id'

            if value in ('with_deals', 'without_deals'):
                pending_deals_qs = Deal.objects.filter(account_id__in=account_ids, status=Deal.PENDING).order_by(field_name)
                item_ids = [
                    deal_id for deal_id in list(
                        pending_deals_qs.distinct(field_name).values_list(field_name, flat=True)
                    ) if deal_id
                ]

                if value == 'with_deals':
                    qs = qs.filter(id__in=item_ids)
                elif value == 'without_deals':
                    qs = qs.exclude(id__in=item_ids)
            elif value in ('with_tasks', 'without_tasks'):
                pending_tasks_qs = Task.objects.filter(account_id__in=account_ids, state__in=[Task.STATE_PENDING, Task.STATE_OVERDUE]).order_by(field_name)
                item_ids = [
                    task_id for task_id in list(
                        pending_tasks_qs.distinct(field_name).values_list(field_name, flat=True)
                    ) if task_id
                ]

                if value == 'with_tasks':
                    qs = qs.filter(id__in=item_ids)
                elif value == 'without_tasks':
                    qs = qs.exclude(id__in=item_ids)
            elif value == 'duplicates':
                scoped_qs = self.model.objects.filter(account_id__in=account_ids)
                distinct_ids = scoped_qs.order_by('name').distinct('name')
                duplicate_names = list(scoped_qs.exclude(id__in=distinct_ids).values_list('name', flat=True))
                qs = qs.filter(name__in=duplicate_names)

        return qs


class CompanyFilterSet(BaseItemFilerSet):
    model_name = ItemType.COMPANY.value
    extra_field_links_queryset = ItemExtraFieldLink.objects.filter(item_type=ItemType.COMPANY.value)

    responsibles = ResponsiblesFilter()
    tags = TagsFilter()
    user = django_filters.ModelChoiceFilter(queryset=User.objects.filter(is_active=True))
    created_at = DateRangeFilter()
    misc = ContactsMiscFilter()

    class Meta:
        model = Company
        fields = (
            'name', 'address', 'website', 'tags', 'responsibles', 'details', 'user',
            'created_at', 'misc',
        )


class PersonFilterSet(BaseItemFilerSet):
    model_name = ItemType.PERSON.value
    extra_field_links_queryset = ItemExtraFieldLink.objects.filter(item_type=ItemType.PERSON.value)

    company = django_filters.ModelChoiceFilter(queryset=Company.objects.all())
    responsibles = ResponsiblesFilter()
    tags = TagsFilter()
    user = django_filters.ModelChoiceFilter(queryset=User.objects.filter(is_active=True))
    created_at = DateRangeFilter()
    misc = ContactsMiscFilter()

    class Meta:
        model = Person
        fields = (
            'name', 'post', 'tags', 'responsibles', 'details', 'user', 'created_at',
            'company', 'misc',
        )
