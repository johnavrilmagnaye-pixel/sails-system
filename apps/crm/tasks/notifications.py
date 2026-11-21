from celery.utils.log import get_task_logger

from project.celery import app

from accounts.models import Account
from crm.models import Deal, Task
from notifications.helpers import NotificationsHelper


logger = get_task_logger(__name__)


__all__ = (
    'notifications_deal_added',
    'notifications_task_added',
)


@app.task(name='crm.notifications_deal_added')
def notifications_deal_added(account_id, deal_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        return

    try:
        deal = Deal.objects.by_account(account).get(id=deal_id)
    except Deal.DoesNotExist:
        return

    if deal.is_user_responsible(deal.user_id):
        return

    # TODO: to whom we should send notification ?
    # NotificationsHelper.crm.deal_added(account, deal.user, deal)


@app.task(name='crm.notifications_task_added')
def notifications_task_added(account_id, task_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        return

    try:
        task = Task.objects.by_account(account).get(id=task_id)
    except Task.DoesNotExist:
        return

    if task.is_user_responsible(task.user_id):
        return

    # TODO: to whom we should send notification ?
    # NotificationsHelper.crm.task_added(account, task.user, task)
