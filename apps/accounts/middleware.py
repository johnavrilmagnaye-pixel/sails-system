from django.utils import timezone as tz
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

from accounts.models import UserAccountLink


class TimezoneMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_link = getattr(request, 'user_link', None)
        if not user_link:
            return
        tz.activate(user_link.timezone)

    def process_response(self, request, response):
        tz.deactivate()
        return response

    def process_exception(self, request, exception):
        tz.deactivate()


class LanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_link = getattr(request, 'user_link', None)
        if not user_link:
            return

        translation.activate(user_link.language)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        translation.deactivate()
        return response

    def process_exception(self, request, exception):
        translation.deactivate()


class AccountMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        request.user_link = None
        request.account = None

        selected_link = self._get_or_select_link(request.user)
        if selected_link is None:
            return None

        request.user_link = selected_link
        request.account = selected_link.account

    @staticmethod
    def _get_or_select_link(user):
        selected_link = UserAccountLink.objects.get_link_by_user(user)
        if selected_link is None:
            return None

        if not selected_link.is_selected:
            selected_link.select_link()

        return selected_link
