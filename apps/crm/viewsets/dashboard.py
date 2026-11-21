from django.db.models import Sum

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from crm.filters import ActivityFilterSet
from crm.filters.base import parse_date_range
from crm.models import Activity, Company, Person, Deal, Task, DealCurrency, get_verbose_budget


__all__ = (
    'DashboardViewSet',
)


class DashboardViewSet(GenericViewSet):
    filterset_class = ActivityFilterSet

    @action(detail=False, methods=['GET'])
    def stats(self, request, *args, **kwargs):
        period = request.query_params.get('created_at')
        date_range = parse_date_range(period)

        stats = {
            'new_companies_cnt': Company.objects.by_account(request.account).filter(created_at__range=date_range).count(),
            'new_persons_cnt': Person.objects.by_account(request.account).filter(created_at__range=date_range).count(),

            'new_tasks_cnt': Task.objects.by_account(request.account).filter(created_at__range=date_range).count(),
            'completed_tasks_cnt': Task.objects.by_account(request.account).filter(state=Task.STATE_COMPLETED, updated_at__range=date_range).count(),
        }

        new_deals_qs = Deal.objects.by_account(request.account).filter(created_at__range=date_range)
        currency_budget_map = {}
        currencies = DealCurrency.objects.filter(
            id__in=new_deals_qs.distinct('currency_id').values_list('currency_id', flat=True).order_by('currency_id')
        )
        for currency in currencies:
            currency_budget_map[currency] = new_deals_qs.filter(
                currency_id=currency.id
            ).aggregate(total=Sum('budget'))['total']
        stats['new_deals_cnt'] = new_deals_qs.count()
        stats['new_deals_budget'] = ' + '.join(
            [get_verbose_budget(budget, currency) for currency, budget in currency_budget_map.items()]
        )

        pending_deals_qs = Deal.objects.by_account(request.account).filter(status=Deal.PENDING)
        currency_budget_map = {}
        currencies = DealCurrency.objects.filter(
            id__in=pending_deals_qs.distinct('currency_id').values_list('currency_id', flat=True).order_by('currency_id')
        )
        for currency in currencies:
            currency_budget_map[currency] = pending_deals_qs.filter(
                currency_id=currency.id
            ).aggregate(total=Sum('budget'))['total']
        stats['pending_deals_cnt'] = pending_deals_qs.count()
        stats['pending_deals_budget'] = ' + '.join(
            [get_verbose_budget(budget, currency) for currency, budget in currency_budget_map.items()]
        )

        return Response({
            'stats_data': stats,
        })

    @action(detail=False, methods=['GET'])
    def activity(self, request, *args, **kwargs):
        actions = Activity.objects.by_account(request.account).select_related('user', 'content_type').prefetch_related('item')
        actions = self.filter_queryset(actions)

        content_type = request.query_params.get('content_type')
        if content_type:
            actions = actions.filter(content_type__model=content_type)

        data = [action.serialize() for action in self.paginate_queryset(actions)]

        return self.get_paginated_response(data)
