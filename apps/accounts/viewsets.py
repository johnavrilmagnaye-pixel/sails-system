from django.contrib.auth.models import User, Permission
from django.db import IntegrityError, transaction
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.utils import email_admins

from accounts.const import UserPermission
from accounts.models import Intro, UserAccountLink
from notifications.helpers import NotificationsHelper


class IntroViewSet(GenericViewSet):
    def list(self, request):
        return Response(request.account.intro.serialize())

    @action(detail=False, methods=['post'])
    def skip_step(self, request):
        intro = request.account.intro

        if intro.current_step == Intro.STEP_USERS:
            intro.set_step(Intro.STEP_IMPORT)
        elif intro.current_step == Intro.STEP_IMPORT:
            intro.complete()

        return Response({})

    @action(detail=False, methods=['post'])
    def invite_users(self, request):
        data = request.data

        emails = data.get('emails', [])
        if not emails:
            return Response({'error': _('Invalid request')}, status=400)

        emails = [email for email in emails if email and email != request.user.email]
        if not emails:
            return Response({'error': _("The user's email address must be different from yours")}, status=400)

        for email in emails:
            try:
                with transaction.atomic():
                    normalized_email = User.objects.normalize_email(email)
                    new_user = User.objects.filter(email__iexact=normalized_email).first()
                    if new_user is None:
                        new_user = User.objects.create_user(username=normalized_email, email=normalized_email)
                        new_user.set_unusable_password()
                        new_user.save(update_fields=('password',))
                    user_link, created = UserAccountLink.objects.get_or_create(
                        user=new_user,
                        account=request.account,
                        defaults={'is_active': False, 'is_invited': True},
                    )
                    if not created:
                        if user_link.is_active and not user_link.is_invited:
                            continue
                        user_link.is_active = False
                        user_link.is_invited = True
                        user_link.save(update_fields=('is_active', 'is_invited', 'updated_at'))
            except IntegrityError as e:
                email_admins(
                    'Integrity error in InviteUserForm',
                    'Account - {}\nError message: {}'.format(
                        request.account.name,
                        smart_str(e)
                    )
                )
                continue

            NotificationsHelper.user_invite(request.account, user_link)

        request.account.intro.set_step(Intro.STEP_IMPORT)

        return Response({})

    @action(detail=False, methods=['post'])
    def complete(self, request):
        request.account.intro.complete()
        return Response({})


class UsersViewSet(GenericViewSet):
    def list(self, request):
        user_links = UserAccountLink.objects.by_account(request.account).select_related('user').order_by(
            'is_invited', '-is_active', 'id'
        )
        return Response([user_link.serialize() for user_link in user_links])

    @action(detail=False, methods=['get'])
    def current(self, request):
        return Response(request.user_link.serialize())

    @action(detail=True, methods=['post'])
    def edit_permissions(self, request, pk):
        try:
            user_link = UserAccountLink.objects.by_account(request.account).get(id=pk)
        except UserAccountLink.DoesNotExist:
            return Response(status=400)

        permissions = request.data.get('permissions')
        if not isinstance(permissions, list):
            return Response({'permissions': _('This field must be a list.')}, status=400)

        allowed_codenames = {permission.value for permission in UserPermission}
        requested_codenames = set(permissions)
        if not requested_codenames.issubset(allowed_codenames):
            return Response({'permissions': _('Invalid permissions.')}, status=400)

        permission_objects = Permission.objects.filter(
            content_type__app_label='crm',
            codename__in=requested_codenames,
        )
        if permission_objects.count() != len(requested_codenames):
            return Response({'permissions': _('Invalid permissions.')}, status=400)

        user_link.permissions.set(permission_objects)
        return Response({
            'user': user_link.serialize(),
        })
