import datetime as dt
import pytz

from django.conf import settings

import django_filters

from crm.models import ExtraField, Tag, ItemResponsibleLink, ItemTagLink


def parse_date_range(value):
    start, end = (part.strip() for part in value.split(' - ', 1))

    def parse_date(date_value):
        for date_format in settings.DATE_INPUT_FORMATS:
            try:
                return dt.datetime.strptime(date_value, date_format)
            except ValueError:
                continue
        raise ValueError(
            "Date {!r} does not match any configured input format".format(date_value)
        )

    return [
        # TODO: use user's timezone
        pytz.timezone(settings.TIME_ZONE).localize(parse_date(start)),
        pytz.timezone(settings.TIME_ZONE).localize(parse_date(end) + dt.timedelta(days=1)),
    ]


class DateRangeFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if value:
            qs = qs.filter(**{'{}__range'.format(self.field_name): parse_date_range(value)})

        return qs


class NumberRangeFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if value:
            value_start = value.split('-')[0].strip()
            if value_start:
                qs = qs.filter(**{'{}__gte'.format(self.field_name): value_start})

            value_end = value.split('-')[1].strip()
            if value_end:
                qs = qs.filter(**{'{}__lte'.format(self.field_name): value_end})

        return qs


class ExtraFieldFilter(django_filters.CharFilter):
    def __init__(self, *args, **kwargs):
        self.links_queryset = kwargs.pop('links_queryset')
        super().__init__(self, *args, **kwargs)

    def filter(self, qs, value):
        if value:
            qs = qs.filter(
                id__in=self.links_queryset.filter(value__icontains=value).values('item_id')
            )

        return qs


class ExtraFieldDateRangeFilter(django_filters.CharFilter):
    def __init__(self, *args, **kwargs):
        self.links_queryset = kwargs.pop('links_queryset')
        super().__init__(self, *args, **kwargs)

    def filter(self, qs, value):
        if value:
            # TODO: use user timezone
            date_range = [
                dt.datetime.strptime(value.split('-')[0].strip(), settings.DATE_INPUT_FORMATS[0]),
                dt.datetime.strptime(
                    value.split('-')[1].strip(), settings.DATE_INPUT_FORMATS[0]
                ) + dt.timedelta(days=1)
            ]

            qs = qs.filter(
                id__in=self.links_queryset.filter(dt_value__range=date_range).values('item_id')
            )

        return qs


class ExtraFieldNumberRangeFilter(django_filters.CharFilter):
    def __init__(self, *args, **kwargs):
        self.links_queryset = kwargs.pop('links_queryset')
        super().__init__(self, *args, **kwargs)

    def filter(self, qs, value):
        if value:
            links_queryset = self.links_queryset

            value_start = value.split('-')[0].strip()
            if value_start:
                links_queryset = links_queryset.filter(number_value__gte=value_start)

            value_end = value.split('-')[1].strip()
            if value_end:
                links_queryset = links_queryset.filter(number_value__lte=value_end)

            if value_start or value_end:
                qs = qs.filter(id__in=links_queryset.values('item_id'))

        return qs


class ExtraFieldJsonFilter(django_filters.CharFilter):
    def __init__(self, *args, **kwargs):
        self.links_queryset = kwargs.pop('links_queryset')
        super().__init__(self, *args, **kwargs)

    def filter(self, qs, value):
        if value:
            qs = qs.filter(
                id__in=self.links_queryset.filter(json_value__icontains=value).values('item_id')
            )

        return qs


class TagsFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value:
            account_id = qs.values_list('account_id', flat=True).first()
            if value == 'isnull':
                has_tags_qs = ItemTagLink.objects.filter(
                    account_id=account_id,
                    item_type=qs.model.ITEM_TYPE
                ).distinct('item_id').values('item_id')
                qs = qs.exclude(id__in=has_tags_qs)
            else:
                try:
                    tag_id = Tag.objects.get(account_id=account_id, name=value).id
                except Tag.DoesNotExist:
                    tag_id = None

                items_qs = ItemTagLink.objects.filter(
                    account_id=account_id,
                    item_type=qs.model.ITEM_TYPE,
                    tag_id=tag_id
                ).values('item_id')
                qs = qs.filter(id__in=items_qs)

        return qs


class ResponsiblesFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value:
            account_id = qs.values_list('account_id', flat=True).first()
            if value == 'isnull':
                has_responsibles_qs = ItemResponsibleLink.objects.filter(
                    account_id=account_id,
                    item_type=qs.model.ITEM_TYPE
                ).distinct('item_id').values('item_id')
                qs = qs.exclude(id__in=has_responsibles_qs)
            else:
                items_qs = ItemResponsibleLink.objects.filter(
                    account_id=account_id,
                    item_type=qs.model.ITEM_TYPE,
                    user_id=int(value)
                ).values('item_id')
                qs = qs.filter(id__in=items_qs)

        return qs


class BaseItemFilerSet(django_filters.FilterSet):
    model_name = None
    extra_field_links_queryset = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        account = getattr(self.request, 'account', None)
        for filter_name in ('company', 'person', 'deal', 'stage', 'currency'):
            model_filter = self.filters.get(filter_name)
            if account and model_filter and hasattr(model_filter.field, 'queryset'):
                model_filter.field.queryset = model_filter.field.queryset.by_account(account)
        user_filter = self.filters.get('user')
        if account and user_filter and hasattr(user_filter.field, 'queryset'):
            user_filter.field.queryset = user_filter.field.queryset.filter(
                useraccountlink__account=account,
                useraccountlink__is_active=True,
            ).distinct()

        extra_fields = ExtraField.objects.filter(content_type__model=self.model_name)
        links_queryset = self.extra_field_links_queryset
        if account:
            extra_fields = extra_fields.by_account(account)
            links_queryset = links_queryset.by_account(account)

        for extra_field in extra_fields:
            field_name = 'extra_field_{}'.format(extra_field.id)

            if extra_field.is_dt:
                self.filters[field_name] = ExtraFieldDateRangeFilter(
                    label=extra_field.name,
                    links_queryset=links_queryset.filter(field=extra_field)
                )
            elif extra_field.is_number:
                self.filters[field_name] = ExtraFieldNumberRangeFilter(
                    label=extra_field.name,
                    links_queryset=links_queryset.filter(field=extra_field)
                )
            elif extra_field.is_json:
                self.filters[field_name] = ExtraFieldJsonFilter(
                    label=extra_field.name,
                    links_queryset=links_queryset.filter(field=extra_field)
                )
            else:
                self.filters[field_name] = ExtraFieldFilter(
                    label=extra_field.name,
                    links_queryset=links_queryset.filter(field=extra_field)
                )
