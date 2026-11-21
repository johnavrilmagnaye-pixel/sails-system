from project.celery import app

from accounts.models import Account
from crm.tasks.base import remind_tasks, clean_archived_items, send_tasks_digest


__all__ = (
    'remind_tasks_starter',
    'send_tasks_digest_starter',
    'clean_archived_items_starter',
)


@app.task(name='crm.remind_tasks_starter')
def remind_tasks_starter():
    account_ids = list(
        Account.objects.all().values_list('id', flat=True)
    )
    for account_id in account_ids:
        remind_tasks.delay(account_id)


@app.task(name='crm.send_tasks_digest_starter')
def send_tasks_digest_starter():
    account_ids = list(
        Account.objects.all().values_list('id', flat=True)
    )
    for account_id in account_ids:
        send_tasks_digest.delay(account_id)


@app.task(name='crm.clean_archived_items_starter')
def clean_archived_items_starter():
    account_ids = list(
        Account.objects.all().values_list('id', flat=True)
    )
    for account_id in account_ids:
        clean_archived_items.delay(account_id)
