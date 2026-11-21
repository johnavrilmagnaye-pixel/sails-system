from django.apps import apps


class ItemsHelper:
    ITEM_MODEL_NAMES = {
        'company': 'Company',
        'person': 'Person',
        'deal': 'Deal',
        'task': 'Task',
        'periodic_task': 'PeriodicTask',
    }

    @classmethod
    def get_model(cls, item_type):
        model_name = cls.ITEM_MODEL_NAMES.get(item_type)
        return apps.get_model('crm', model_name) if model_name else None

    @classmethod
    def fetch_item(cls, account, item_type, item_id):
        model = cls.get_model(item_type)
        if model is None:
            raise KeyError(item_type)

        try:
            item = model.objects.by_account(account).get(id=item_id)
        except model.DoesNotExist:
            item = None

        return item
