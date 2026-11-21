from rest_framework.permissions import BasePermission


class AccountRequiredPermission(BasePermission):
    message = 'An active account is required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request, 'account', None) is not None
            and getattr(request, 'user_link', None) is not None
        )


class AccountObjectPermission(AccountRequiredPermission):
    """ Disallows access to objects that do not belong to the request account """
    message = "You don't have permission to access this object."

    def has_object_permission(self, request, view, obj):
        account = request.account
        object_account_id = getattr(obj, 'account_id', None)
        return object_account_id is not None and object_account_id == account.id
