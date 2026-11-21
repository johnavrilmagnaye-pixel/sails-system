from django.db import IntegrityError
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.helpers import AccountHelper
from accounts.models import Account, UserAccountLink


class AccountListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user_links = UserAccountLink.objects.active().filter(
            user=request.user,
            account__is_archived=False,
        ).select_related('account').order_by('account__name', 'account_id')
        response_data = [user_link.serialize_account() for user_link in user_links]
        return Response(response_data)


class CurrentAccountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user_link = getattr(request, 'user_link', None)
        if user_link is None:
            return Response({'error': _('No active account is selected.')}, status=status.HTTP_404_NOT_FOUND)
        return Response(user_link.serialize_account())


class SwitchAccountView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        account_id = request.data.get('account_id')
        if not account_id:
            return Response(
                {'errors': {'account_id': _('This field is required.')}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_links = UserAccountLink.objects.active().filter(
            user=request.user,
            account__is_archived=False,
        )
        try:
            target_link = user_links.select_related('account').get(account_id=account_id)
        except (TypeError, ValueError, UserAccountLink.DoesNotExist):
            return Response(
                {'error': _('Account not found.')},
                status=status.HTTP_404_NOT_FOUND,
            )

        target_link.select_link()

        return Response(target_link.serialize_account())


class CreateAccountView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        name = str(request.data.get('name', '')).strip()
        if not name:
            return Response(
                {'errors': {'name': _('This field is required.')}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            account = AccountHelper.create(name=name, user=request.user)
        except IntegrityError:
            return Response(
                {'errors': {'name': _('An account with this name already exists.')}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_link = UserAccountLink.objects.by_account(account).select_related('account').get(
            user=request.user,
        )
        return Response(user_link.serialize_account(), status=status.HTTP_201_CREATED)
