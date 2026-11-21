from urllib.parse import urljoin

from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from accounts.models import get_user_account_name

from .crm import CRMNotificationsHelper


class NotificationsHelper(object):
    crm = CRMNotificationsHelper

    @classmethod
    def user_invite(cls, account, user_link):
        activation_url = urljoin(
            settings.APP_URL.rstrip('/') + '/',
            user_link.get_activation_url().lstrip('/'),
        )
        context = {
            'account': account,
            'activation_url': activation_url,
        }
        user_link.email_user('user_invite', context, settings.FROM_EMAIL['welcome'])

    @classmethod
    def task_reminder(cls, account, user_link, task):
        if user_link.notification_settings.remind_task:
            task_owner_user = task.user

            context = {
                'account': account,
                'user_link': user_link,
                'task': task,
                'url': task.get_full_url(account, urlconf='crm.urls'),
            }
            headers = {
                'Reply-To': '{0} <{1}>'.format(
                    get_user_account_name(account, task_owner_user),
                    task_owner_user.email,
                )
            }
            user_link.email_user('task_reminder', context, settings.FROM_EMAIL['remind'], headers=headers)

        user_link.add_notification(
            mark_safe(
                _('Task reminder: <a href="{0}">{1}</a>').format(
                    task.get_absolute_url(urlconf='crm.urls'), task.name
                )
            )
        )

    @classmethod
    def responsible_assigned(cls, account, user_link, item, assigned_by_name):
        if user_link.notification_settings.notify_item_responsibles[item.ITEM_TYPE]:
            item_owner_user = item.user

            context = {
                'account': account,
                'user_link': user_link,
                'item': item,
                'item_url': item.get_full_url(account, urlconf='crm.urls'),
                'assigned_by_name': assigned_by_name,
            }
            headers = {
                'Reply-To': '{} <{}>'.format(
                    get_user_account_name(account, item_owner_user),
                    item_owner_user.email,
                )
            }
            user_link.email_user(
                'responsible_assigned/{}'.format(item.ITEM_TYPE),
                context, settings.FROM_EMAIL['notify'], headers=headers
            )

            user_link.add_notification(
                mark_safe(
                    _('You have been assigned to {}: <a href="{}">{}</a>').format(
                        item.ACCUSATIVE, item.get_absolute_url(urlconf='crm.urls'), item
                    )
                )
            )

    @classmethod
    def tasks_digest(cls, account, user_link, tasks):
        for task in tasks:
            task.url = task.get_full_url(account, urlconf='crm.urls')

        context = {
            'account': account,
            'user_link': user_link,
            'tasks': tasks,
        }
        user_link.email_user('tasks_digest', context, settings.FROM_EMAIL['remind'])
