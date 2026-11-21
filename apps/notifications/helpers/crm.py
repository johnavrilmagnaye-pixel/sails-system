from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from accounts.models import UserAccountLink, get_user_account_name


class CRMNotificationsHelper(object):
    @staticmethod
    def _get_user_link(account, user):
        return UserAccountLink.objects.get_link_by_user(user, account=account)

    @classmethod
    def deal_added(cls, account, user, deal):
        user_link = cls._get_user_link(account, user)
        if user_link is None:
            return

        context = {
            'account': account,

            'deal_name': deal.name,
            'deal_user_name': get_user_account_name(account, deal.user),
            'deal_verbose_budget': deal.verbose_budget,
            'deal_details': deal.details,
            'deal_url': deal.get_full_url(account, urlconf='crm.urls'),
            'deal_company': deal.company.name if deal.company else None,
            'deal_person': deal.person.name if deal.person else None,
        }
        user_link.email_user('crm/deal_added', context, settings.FROM_EMAIL['notify'])

        user_link.add_notification(
            mark_safe(
                _('New deal: <a href="{}">{}</a>').format(
                    deal.get_absolute_url(urlconf='crm.urls'), deal.name
                )
            )
        )

    @classmethod
    def deal_closed(cls, account, user, deal):
        user_link = cls._get_user_link(account, user)
        if user_link is None:
            return

        context = {
            'account': account,
            'user_link': user_link,
            'deal': deal,
            'url': deal.get_full_url(account, urlconf='crm.urls'),
        }
        user_link.email_user('crm/deal_closed', context, settings.FROM_EMAIL['notify'])

        user_link.add_notification(
            mark_safe(
                _('Deal {}: <a href="{}">{}</a>').format(
                    deal.get_status_display().lower(), deal.get_absolute_url(urlconf='crm.urls'), deal.name
                )
            )
        )

    @classmethod
    def task_added(cls, account, user, task):
        user_link = cls._get_user_link(account, user)
        if user_link is None:
            return

        deadline_dt = task.expire_date.astimezone(user_link.timezone) if task.expire_date else None
        context = {
            'account': account,

            'task_name': task.numbered_name,
            'task_user_name': get_user_account_name(account, task.user),
            'task_deadline': deadline_dt.strftime(settings.DATETIME_INPUT_FORMATS[0]) if deadline_dt else None,
            'task_details': task.details,
            'task_url': task.get_full_url(account, urlconf='crm.urls'),
            'task_company': task.company.name if task.company else None,
            'task_person': task.person.name if task.person else None,
            'task_deal': task.deal.name if task.deal else None,
        }
        user_link.email_user('crm/task_added', context, settings.FROM_EMAIL['notify'])

        user_link.add_notification(
            mark_safe(
                _('New task: <a href="{}">{}</a>').format(
                    task.get_absolute_url(urlconf='crm.urls'), task.numbered_name
                )
            )
        )

    @classmethod
    def task_completed(cls, account, task, completed_by_user):
        user_link = cls._get_user_link(account, task.user)
        if user_link is None:
            return

        headers = {
            'Reply-To': '{} <{}>'.format(
                get_user_account_name(account, completed_by_user),
                completed_by_user.email,
            )
        }
        context = {
            'account': account,
            'user_link': user_link,
            'task': task,
            'url': task.get_full_url(account, urlconf='crm.urls'),
            'completed_by_user': completed_by_user,
            'completed_by_name': get_user_account_name(account, completed_by_user),
        }

        if user_link.notification_settings.notify_task_completed:
            user_link.email_user(
                'crm/task_completed', context, settings.FROM_EMAIL['notify'], headers=headers
            )

        user_link.add_notification(
            mark_safe(
                _('Task completed: <a href="{}">{}</a>').format(
                    task.get_absolute_url(urlconf='crm.urls'), task.numbered_name
                )
            )
        )

    @classmethod
    def note_added(cls, account, user, note, model_name):
        user_link = cls._get_user_link(account, user)
        if user_link is None:
            return

        item = note.item
        note_owner_user = item.user

        context = {
            'account': account,
            'user_link': user_link,
            'note': note,
            'note_user_name': get_user_account_name(account, note.user),
            'item': item,
            'item_url': item.get_full_url(account, urlconf='crm.urls')
        }
        headers = {
            'Reply-To': '{} <{}>'.format(
                get_user_account_name(account, note_owner_user),
                note_owner_user.email,
            )
        }

        if getattr(user_link.notification_settings, 'notify_{}_note'.format(model_name)):
            user_link.email_user(
                'crm/note_added/{}'.format(model_name),
                context,
                settings.FROM_EMAIL['notify'],
                headers=headers,
            )

            user_link.add_notification(
                mark_safe(_('New note for {}: <a href="{}">{}</a>').format(
                    item.DATIVE, item.get_absolute_url(urlconf='crm.urls'), item.name)
                )
            )
