from django.conf import settings
from django.contrib.auth import login
from django.utils.translation import gettext as _

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.forms import UserProfileForm
from accounts.models import Intro, UserAccountLink
from notifications.helpers import NotificationsHelper


class UserOptionsView(GenericAPIView):
    queryset = UserAccountLink.objects.active().select_related('user')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')

    def get(self, request):
        links = self.filter_queryset(self.get_queryset().by_account(request.account))
        return Response([link.option_serialize() for link in links])


class EditProfileAPI(APIView):
    def post(self, request):
        form = UserProfileForm(data=request.data, instance=request.user)
        if not form.is_valid():
            return Response(data={
                'errors': form.errors,
            }, status=400)

        user = request.user
        cleaned_data = form.cleaned_data
        user.email = cleaned_data['email']
        user.first_name = cleaned_data['first_name']
        user.last_name = cleaned_data['last_name']
        user.save(update_fields=('email', 'first_name', 'last_name'))

        user_link = request.user_link
        user_link.user = user
        user_link.timezone = cleaned_data['timezone']
        user_link.language = cleaned_data['language']
        user_link.save(update_fields=('timezone', 'language', 'updated_at'))

        intro = Intro.objects.by_account(request.account).first()
        if intro is not None and not intro.is_completed:
            intro.set_step(Intro.STEP_USERS)

        response = Response(request.user_link.serialize())
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            request.user_link.language,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
        return response


class ChangePasswordAPI(APIView):
    def post(self, request):
        user = request.user

        current_password = request.data.get('current_password')
        if not user.check_password(current_password):
            return Response(data={
                'errors': {
                    'current_password': _('Enter the correct password'),
                },
            }, status=400)

        new_password = request.data.get('new_password')
        if not new_password:
            return Response(data={
                'errors': {
                    'new_password': _('Password cannot be empty'),
                },
            }, status=400)

        user.set_password(new_password)
        user.save(update_fields=('password',))

        login(request, user)

        return Response({})


class ResendInviteAPI(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({
                'error': _('No user specified')
            }, status=400)

        try:
            user_link = UserAccountLink.objects.by_account(request.account).get(id=user_id)
        except UserAccountLink.DoesNotExist:
            return Response({
                'error': _('This user does not exist')
            }, status=400)

        NotificationsHelper.user_invite(request.account, user_link)

        return Response()
