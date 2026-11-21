import datetime as dt

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils.translation import gettext as _

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.decorators import admin_required, owner_required

from accounts.const import UserRole
from accounts.models import UserAccountLink
from crm.const import ItemType
from crm.filters import FunnelFilterSet, BaseTaskFilterSet
from crm.models import (
    Deal, Task, DealCurrency, DealStage, get_verbose_budget, Person, Company, ItemResponsibleLink,
)
from crm.utils import get_conversion


class DealsBoardView(GenericAPIView):
    filterset_class = FunnelFilterSet
    ordering_fields = (
        'name', 'company__name', 'person__name', 'status', 'stage', 'budget', 'tags', 'details', 'user', 'created_at',
    )
    search_fields = ('name', 'company__name', 'person__name', 'details',)

    def get_queryset(self):
        user = self.request.user

        deals_qs = Deal.objects.by_account(self.request.account).filter(
            status=Deal.PENDING
        ).select_related(
            'company', 'person', 'currency', 'stage', 'user'
        ).only(
            'id', 'name',  'status', 'budget', 'details', 'created_at',
            'company_id', 'company__name', 'person_id', 'person__name',
            'stage', 'currency',
            'user_id', 'user__email', 'user__first_name', 'user__last_name'
        )

        if not self.request.user_link.has_perm('view_all_deal'):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(self.request.account).filter(
                item_type=ItemType.DEAL.value,
                user_id=user.id
            ).values('item_id')
            deals_qs = deals_qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        return deals_qs

    def get(self, request, *args, **kwargs):
        deals_qs = self.filter_queryset(self.get_queryset())

        board_data = {}
        currencies = list(
            DealCurrency.objects.by_account(request.account).filter(
                id__in=deals_qs.distinct('currency_id').values_list('currency_id', flat=True).order_by('currency_id')
            )
        )
        deal_stages = list(DealStage.objects.by_account(request.account))
        for stage in deal_stages:
            stage_deals_qs = deals_qs.filter(stage=stage)

            currency_budget_map = {}
            for currency in currencies:
                currency_budget_map[currency] = stage_deals_qs.filter(
                    currency_id=currency.id
                ).aggregate(total=Sum('budget'))['total']

            board_data[stage.id] = {
                'name': stage.name,
                'position': stage.position,
                'deals': [deal.serialize() for deal in stage_deals_qs],
                'budget': ' + '.join([
                     get_verbose_budget(budget, currency) for currency, budget in
                     currency_budget_map.items() if budget
                ])
            }

        return Response(board_data)


class DealsFunnelView(GenericAPIView):
    filterset_class = FunnelFilterSet
    search_fields = ('name', 'company__name', 'person__name', 'details',)

    def get_queryset(self):
        user = self.request.user

        deals_qs = Deal.objects.by_account(self.request.account).filter(
            status__in=(Deal.COMPLETED, Deal.FAILED)
        ).select_related('currency', 'stage')

        if not self.request.user_link.has_perm('view_all_deal'):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(self.request.account).filter(
                item_type=ItemType.DEAL.value,
                user_id=user.id
            ).values('item_id')
            deals_qs = deals_qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        return deals_qs

    def get(self, request, *args, **kwargs):
        deals = self.filter_queryset(self.get_queryset())

        if not deals.exists():
            return Response(data={
                'chart_data': [],
                'table_data': {},
            })

        failed = deals.filter(status=Deal.FAILED)
        completed = deals.filter(status=Deal.COMPLETED)
        completed_number = completed.count()

        deal_currencies = DealCurrency.objects.filter(deal__id__in=deals.values_list('id', flat=True)).distinct()

        deal_stages = DealStage.objects.by_account(request.account)
        deals_numbers = []
        for stage in deal_stages:
            deals_numbers.append(failed.filter(stage__position__gte=stage.position).count() + completed_number)

        deals_numbers.append(completed_number)

        stages = []
        for stage in deal_stages:
            stage_data = {
                'position': stage.position + 1,
                'name': stage.name,
                'deals_number': deals_numbers[stage.position],
                'conversion': get_conversion(deals_numbers[stage.position + 1], deals_numbers[stage.position]),
                'budgets': [(
                                failed.filter(stage__position__gte=stage.position, currency_id=currency.id).aggregate(
                                    Sum('budget'))['budget__sum'] or 0) + (
                                completed.filter(currency_id=currency.id).aggregate(Sum('budget'))['budget__sum'] or 0
                            ) for currency in deal_currencies]
            }
            stages.append(stage_data)

        total_budgets = [
            completed.filter(
                currency_id=currency.id
            ).aggregate(Sum('budget'))['budget__sum'] or 0 for currency in deal_currencies
        ]

        chart_data = None
        if deals.exists():
            chart_data = {
                'labels': [],
                'datasets': [{
                    'backgroundColor': '#428bca',
                    'data': [],
                }]
            }

            for stage in DealStage.objects.by_account(request.account):
                chart_data['labels'].append(stage.name)
                chart_data['datasets'][0]['data'].append(
                    failed.filter(stage__position__gte=stage.position).count() + completed_number
                )

            chart_data['labels'].append(_('Successfully completed'))
            chart_data['datasets'][0]['data'].append(completed_number)

        return Response(data={
            'chart_data': chart_data,
            'table_data': {
                'stages': stages,
                'deal_currencies': [deal_currency.serialize() for deal_currency in deal_currencies],
                'total_conversion': get_conversion(completed_number, deals.count()),
                'total_budgets': total_budgets,
            },
        })


class TasksCalendarView(GenericAPIView):
    filterset_class = BaseTaskFilterSet
    search_fields = ('id', 'name', 'company__name', 'person__name', 'details',)

    def get_queryset(self):
        user = self.request.user

        tasks_qs = Task.objects.by_account(self.request.account).filter(
            state__in=(Task.STATE_PENDING, Task.STATE_OVERDUE),
            expire_date__isnull=False
        )

        if not self.request.user_link.has_perm('view_all_task'):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(self.request.account).filter(
                item_type=ItemType.TASK.value,
                user_id=user.id
            ).values('item_id')
            tasks_qs = tasks_qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        start = self.request.query_params.get('start')
        if start:
            start_date = dt.datetime.strptime(start, '%Y-%m-%d')
            tasks_qs = tasks_qs.filter(expire_date__gte=start_date)

        end = self.request.query_params.get('end')
        if start:
            end_date = dt.datetime.strptime(end, '%Y-%m-%d')
            tasks_qs = tasks_qs.filter(expire_date__lt=end_date)

        return tasks_qs

    def get(self, request):
        tasks = self.filter_queryset(self.get_queryset())
        return Response([task.calendar_serialize() for task in tasks])


@login_required()
@admin_required()
def update_deal_stages_positions(request):
    if 'data[]' in request.POST:
        data = request.POST.get('data[]').split(',')
        ordering = 'CASE %s END' % ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(data)])
        DealStage.objects.by_account(request.account).filter(id__in=data).extra(select={'ordering': ordering}, order_by=('ordering',)).reposition()

    return JsonResponse({'success': True})


@login_required()
@admin_required()
def change_user_status(request, user_id):
    try:
        target_link = UserAccountLink.objects.by_account(request.account).get(user_link_idid=user_id)
    except UserAccountLink.DoesNotExist:
        return JsonResponse({'success': False})

    if request.user_link.is_admin and request.user_link.id != target_link.id:
        status = request.POST['status']

        target_link.is_active = True if status == 'true' else False
        target_link.save(update_fields=('is_active', 'updated_at'))

        return JsonResponse({
            'success': True
        })

    return JsonResponse({'success': False})


@login_required()
@admin_required()
def change_user_role(request, user_id):
    try:
        account_user = UserAccountLink.objects.by_account(request.account).get(id=user_id)
    except UserAccountLink.DoesNotExist:
        return JsonResponse({'success': False})

    if request.user_link.is_admin and request.user_link != account_user:
        role = request.POST['role']

        account_user.role = UserRole.ADMIN if role == 'admin' else UserRole.MANAGER
        account_user.save(update_fields=('role', 'updated_at'))

        return JsonResponse({
            'success': True
        })

    return JsonResponse({'success': False})


@login_required()
@owner_required()
def make_owner(request, user_id):
    try:
        account_user = UserAccountLink.objects.by_account(request.account).get(id=user_id)
    except UserAccountLink.DoesNotExist:
        return JsonResponse({'success': False})

    if request.user_link.is_owner and request.user_link != account_user:
        with transaction.atomic():
            locked_links = UserAccountLink.objects.select_for_update().filter(
                id__in=(request.user_link.id, account_user.id),
            ).in_bulk()
            new_owner = locked_links[account_user.id]
            old_owner = locked_links[request.user_link.id]
            new_owner.role = UserRole.OWNER
            old_owner.role = UserRole.ADMIN
            new_owner.save(update_fields=('role', 'updated_at'))
            old_owner.save(update_fields=('role', 'updated_at'))

        return JsonResponse({
            'success': True
        })

    return JsonResponse({'success': False})


class ItemOptionsView(GenericAPIView):
    model = None
    filterset_fields = []
    search_fields = ('name',)
    perm = None

    def get_queryset(self):
        request = self.request
        user = request.user

        qs = self.model.objects.by_account(request.account).only('id', 'name')

        if not request.user_link.has_perm(self.perm):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(request.account).filter(
                item_type=self.model.ITEM_TYPE
            ).values('item_id')
            qs = qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        selected = request.query_params.get('selected')
        if selected:
            qs = qs.exclude(id=selected)

        return qs

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        return Response([item.option_serialize() for item in qs])


class CompanyOptionsView(ItemOptionsView):
    model = Company
    perm = 'crm.view_all_company'


class PersonOptionsView(ItemOptionsView):
    model = Person
    filterset_fields = ('company',)
    perm = 'crm.view_all_persons'


class DealOptionsView(ItemOptionsView):
    model = Deal
    filterset_fields = ('company', 'person')
    perm = 'crm.view_all_deals'
