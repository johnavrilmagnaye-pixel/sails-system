from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone as tz
from django.utils.translation import gettext as _

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from accounts.models import Account
from crm.const import ItemType
from crm.filters import DealFilterSet
from crm.forms import DealForm
from crm.models import Activity, Deal, DealCurrency, DealStage, Note, DealStageChange, ItemResponsibleLink
from crm.tasks import notify_responsibles, notifications_deal_added
from crm.viewsets.base import ItemViewSet
from notifications.helpers import NotificationsHelper


__all__ = (
    'DealsViewSet',
    'DealCurrenciesViewSet',
    'DealStagesViewSet',
)


class DealsViewSet(ItemViewSet):
    model = Deal
    filterset_class = DealFilterSet
    ordering_fields = (
        'name', 'company__name', 'person__name', 'status', 'stage', 'budget', 'tags', 'details', 'user', 'created_at',
    )
    search_fields = ('name', 'company__name', 'person__name', 'details',)

    def get_queryset(self):
        user = self.request.user

        deals_qs = Deal.objects.by_account(self.request.account).select_related(
            'company', 'person', 'currency', 'stage', 'user'
        )

        if not self.request.user_link.has_perm('view_all_deal'):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(self.request.account).filter(
                item_type=ItemType.DEAL.value,
                user_id=user.id
            ).values('item_id')
            deals_qs = deals_qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        return deals_qs

    @action(detail=False, methods=['post'])
    def add(self, request):
        form = DealForm(data=request.data, account=request.account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        deal = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.DEAL.value, [deal.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.DEAL.value, [deal.id], [tag.id for tag in tags], 'set')

        notify_responsibles.delay(request.account.id, ItemType.DEAL.value, deal.id, [], request.user_link.name)
        Activity.log_addition(deal)

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.DEAL.value, [deal.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.DEAL.value, [deal.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.DEAL.value, [deal.id]),
        }

        return Response({
            'deal': deal.serialize(**serialize_params),
        })

    @action(detail=True, methods=['post'])
    def edit(self, request, pk):
        try:
            deal = Deal.objects.by_account(request.account).get(id=pk)
        except Deal.DoesNotExist:
            return Response({'error': _('This deal does not exist')}, status=400)

        old_responsible_ids = deal.get_responsible_ids()

        form = DealForm(data=request.data, instance=deal, account=request.account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        deal = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.DEAL.value, [deal.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.DEAL.value, [deal.id], [tag.id for tag in tags], 'set')

        notify_responsibles.delay(request.account.id, ItemType.DEAL.value, deal.id, old_responsible_ids, request.user_link.name)

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.DEAL.value, [deal.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.DEAL.value, [deal.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.DEAL.value, [deal.id]),
        }

        return Response({
            'deal': deal.serialize(**serialize_params),
        })

    @action(detail=True, methods=['post'])
    def complete_stage(self, request, pk):
        try:
            deal = Deal.objects.by_account(request.account).get(id=pk)
        except Deal.DoesNotExist:
            return Response({'error': _('This deal does not exist')}, status=400)

        deal_state_change = DealStageChange(
            account=request.account,
            deal=deal,
            type=DealStageChange.COMPLETE_STAGE,
            previous_stage=deal.stage,
            user=request.user
        )

        stages = DealStage.objects.by_account(request.account)
        if deal.stage == stages.reverse()[0]:
            deal.status = Deal.COMPLETED
            deal_state_change.is_finish_change = True
        else:
            deal.stage = stages.get(position=deal.stage.position + 1)
            deal_state_change.new_stage = deal.stage

        note = Note.objects.create(
            account=request.account,
            item=deal,
            user=request.user,
            text=_('Stage <b>{}</b> completed').format(deal.stage.name)
        )
        if deal.status == Deal.COMPLETED:
            note = Note.objects.create(
                account=request.account,
                item=deal,
                user=request.user,
                text=_('Deal completed')
            )

        deal.updated_at = tz.now()
        deal.save(update_fields=('status', 'stage', 'updated_at'))
        deal_state_change.save()

        return Response({
            'deal': deal.serialize(),
            'note': note.serialize(),
        })

    @action(detail=True, methods=['post'])
    def fail_stage(self, request, pk):
        try:
            deal = Deal.objects.by_account(request.account).get(id=pk)
        except Deal.DoesNotExist:
            return Response({'error': _('This deal does not exist')}, status=400)

        deal.status = Deal.FAILED
        deal.updated_at = tz.now()
        deal.save(update_fields=('status', 'updated_at'))

        if request.account.is_gta:
            user_link = request.account.get_owner()
            NotificationsHelper.crm.deal_closed(request.account, user_link.user, deal)

        note = Note.objects.create(
            account=request.account,
            item=deal,
            user=request.user,
            text=_('Rejected at stage {}').format(deal.stage.name)
        )

        DealStageChange.objects.create(
            account=request.account,
            deal=deal,
            type=DealStageChange.FAIL_STAGE,
            previous_stage=deal.stage,
            user=request.user
        )

        return Response({
            'deal': deal.serialize(),
            'note': note.serialize(),
        })


class DealStagesViewSet(GenericViewSet):
    def list(self, request):
        deal_stages = DealStage.objects.by_account(request.account)

        name = request.query_params.get('name')
        if name:
            deal_stages = deal_stages.filter(name=name)

        return Response([deal_stage.serialize() for deal_stage in deal_stages])

    def create(self, request):
        name = request.data.get('name')
        if not name:
            return Response({'error': _('Invalid request')}, status=400)

        if DealStage.objects.by_account(request.account).filter(name=name).exists():
            return Response({'error': _('A tag with this name already exists')}, status=400)

        deal_stage = DealStage.objects.create(account=request.account, name=name)

        return Response({
            'deal_stage': deal_stage.serialize(),
        })

    @action(detail=True, methods=['POST'])
    def edit(self, request, pk):
        try:
            deal_stage = DealStage.objects.by_account(request.account).get(id=pk)
        except DealStage.DoesNotExist:
            return Response({'error': _('This stage does not exist')}, status=400)

        name = request.data.get('value')
        if not name:
            return Response({'error': _('Invalid request')}, status=400)

        if DealStage.objects.by_account(request.account).filter(name=name).exists():
            return Response({'error': _('A stage with this name already exists')}, status=400)

        deal_stage.name = name
        deal_stage.save(update_fields=('name',))

        return Response({})

    @action(detail=True, methods=['POST'])
    def delete(self, request, pk):
        try:
            deal_stage = DealStage.objects.by_account(request.account).get(id=pk)
        except DealStage.DoesNotExist:
            return Response({'error': _('The stage has already been deleted')}, status=400)

        deal_stage.delete()

        return Response({})


class DealCurrenciesViewSet(GenericViewSet):
    def list(self, request):
        deal_currencies = DealCurrency.objects.by_account(request.account)

        disabled = bool(request.query_params.get('disabled', False))
        deal_currencies = deal_currencies.filter(is_enabled=not disabled)

        name = request.query_params.get('search')
        if name:
            deal_currencies = deal_currencies.filter(name__icontains=name)

        return Response([deal_currency.serialize() for deal_currency in deal_currencies])

    def create(self, request):
        deal_currency_id = request.data.get('deal_currency_id')
        if not deal_currency_id:
            return Response({'error': _('Invalid request')}, status=400)

        try:
            deal_currency = DealCurrency.objects.by_account(request.account).get(
                is_enabled=False,
                id=deal_currency_id
            )
        except DealCurrency.DoesNotExist:
            return Response({'error': _('Invalid request')}, status=400)

        deal_currency.is_enabled = True
        deal_currency.save(update_fields=('is_enabled',))

        return Response({
            'deal_currency': deal_currency.serialize(),
        })

    @action(detail=True, methods=['POST'])
    def delete(self, request, pk):
        try:
            deal_currency = DealCurrency.objects.by_account(request.account).get(id=pk)
        except DealCurrency.DoesNotExist:
            return Response({'error': _('The currency has already been deleted')}, status=400)

        deal_currency.is_enabled = False
        deal_currency.save(update_fields=('is_enabled',))

        return Response({})
