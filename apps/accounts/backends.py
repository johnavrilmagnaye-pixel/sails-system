from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from accounts.models import UserAccountLink


class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if username is None or password is None:
            return None

        email = User.objects.normalize_email(username.strip())
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

        if not user.check_password(password) or not self.user_can_authenticate(user):
            return None

        link = UserAccountLink.objects.get_link_by_user(user)
        if link is None:
            return None

        if not link.is_selected:
            link.select_link()

        return user
