from django.db import models

from accounts.const import UserRole


class UserAccountLinkQuerySet(models.QuerySet):
    def by_account(self, account):
        return self.filter(account=account)

    def active(self):
        return self.filter(
            is_archived=False,
            is_active=True,
        )

    def inactive(self):
        return self.filter(is_active=False)

    def admins(self):
        return self.filter(role__in=(UserRole.OWNER, UserRole.ADMIN))

    def managers(self):
        return self.filter(role=UserRole.MANAGER)


class UserAccountLinkManager(models.Manager.from_queryset(UserAccountLinkQuerySet)):
    def get_link_by_user(self, user, account=None):
        """ Returns selected or most recently used available link for a user """
        links = self.active().filter(
            user=user,
            account__is_archived=False,
        ).select_related('account', 'user')
        if account is not None:
            links = links.by_account(account)

        return links.order_by(
            '-is_selected',
            '-updated_at',
            '-id'
        ).first()
