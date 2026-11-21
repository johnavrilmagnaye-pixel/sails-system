import json
import operator

from django.conf import settings
from django.db.models import Q

from core.singleton.redis_client import redis_client
from functools import reduce


def get_conversion(completed, total):
    try:
        return 100.0 * completed / total
    except ZeroDivisionError:
        return 0


def get_filterset(model_name):
    from crm.filters import CompanyFilterSet, PersonFilterSet, DealFilterSet, TaskFilterSet
    model_filterset_map = {
        'company': CompanyFilterSet,
        'person': PersonFilterSet,
        'deal': DealFilterSet,
        'task': TaskFilterSet,
    }

    return model_filterset_map[model_name]


def get_api_view(model_name):
    from crm.viewsets import CompaniesViewSet, PersonsViewSet, DealsViewSet, TasksViewSet

    model_name_view_map = {
        'company': CompaniesViewSet,
        'person': PersonsViewSet,
        'deal': DealsViewSet,
        'task': TasksViewSet,
    }

    return model_name_view_map[model_name]


def get_batch_qs(model, request=None, data=None):
    filterset = get_filterset(model.ITEM_TYPE)
    api_view = get_api_view(model.ITEM_TYPE)

    qs = model.objects.all().order_by('-created_at')

    if not data:
        if 'data' in request.POST:
            data = json.loads(request.POST['data'])
        else:
            data = request.POST

    query = data.get('query')
    if query:
        if not (isinstance(query, dict)):
            query = json.loads(query)
        qs = filterset(query, qs).qs

        search = query.get('search')
        if search:
            qs = qs.filter(
                reduce(
                    operator.or_,
                    (Q(**{'{}__icontains'.format(field): search}) for field in api_view.search_fields)
                )
            )
    if 'items' in data and data['items']:
        if isinstance(data['items'], list):
            items_ids = data.get('items')
        else:
            items_ids = data.getlist('items')
        if items_ids:
            qs = qs.filter(id__in=items_ids)

    return qs


def _get_contacts_import_data_key(account_id, contacts_import_id):
    return 'contacts_import:rows:{0}:{1}'.format(account_id, contacts_import_id)


def save_contacts_import_data(account_id, contacts_import_id, rows):
    key = _get_contacts_import_data_key(account_id, contacts_import_id)
    contacts_data = json.dumps(rows)
    redis_client.set(key, contacts_data, settings.CONTACTS_IMPORT_DATA_EXPIRE)


def get_contacts_import_data(account_id, contacts_import_id):
    key = _get_contacts_import_data_key(account_id, contacts_import_id)
    contacts_data = redis_client.get(key)
    if not contacts_data:
        return None
    return json.loads(contacts_data)
