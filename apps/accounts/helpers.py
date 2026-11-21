from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import gettext

from accounts.const import DEAL_CURRENCIES, DEFAULT_CURRENCY_CODES, DEFAULT_DEAL_STAGES, UserRole
from accounts.models import Account, Intro, UserAccountLink
from crm.models import DealCurrency, DealStage
from notifications.models import NotificationSettings


class AccountHelper:
    @classmethod
    @transaction.atomic
    def create(cls, name, user=None, email=None, password=None):
        """ Create an account, owner link, intro and default fields """
        if user is None:
            if not email:
                raise ValueError('email is required when user is not provided')

            user = cls._get_or_create_user(email, password)
        else:
            user = User.objects.select_for_update().get(pk=user.pk)

        account = Account.objects.create(name=name)
        Intro.objects.create(account=account)
        cls._create_initial_crm_data(account)

        UserAccountLink.all_objects.filter(user=user).update(is_selected=False)
        owner_link = UserAccountLink.objects.create(
            account=account,
            user=user,
            role=UserRole.OWNER,
            is_active=True,
            is_selected=True,
        )
        NotificationSettings.objects.create(user_link=owner_link)
        return account

    @classmethod
    @transaction.atomic
    def create_owner(cls, account, email, password):
        user = cls._get_or_create_user(email, password)

        Intro.objects.get_or_create(account=account)
        cls._create_initial_crm_data(account)
        UserAccountLink.all_objects.filter(user=user).update(is_selected=False)
        owner_link = UserAccountLink.objects.create(
            account=account,
            user=user,
            role=UserRole.OWNER,
            is_active=True,
            is_selected=True,
        )
        NotificationSettings.objects.create(user_link=owner_link)

        return user

    @staticmethod
    def _get_or_create_user(email, password):
        email = User.objects.normalize_email(email.strip())
        user, created = User.objects.select_for_update().get_or_create(
            email__iexact=email,
            defaults={
                'username': email,
                'email': email,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=('password',))
        return user

    @classmethod
    def _create_initial_crm_data(cls, account):
        for name, position in DEFAULT_DEAL_STAGES:
            DealStage.objects.get_or_create(
                account=account,
                name=gettext(name),
                defaults={'position': position},
            )

        for name, code, format_ in DEAL_CURRENCIES:
            DealCurrency.objects.get_or_create(
                account=account,
                code=code,
                defaults={
                    'name': gettext(name),
                    'format': format_,
                    'is_enabled': code in DEFAULT_CURRENCY_CODES,
                },
            )
