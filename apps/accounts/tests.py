from unittest.mock import patch

from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission, User
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.const import UserPermission, UserRole
from accounts.helpers import AccountHelper
from accounts.middleware import AccountMiddleware, TimezoneMiddleware
from accounts.models import Account, Intro, UserAccountLink
from accounts.viewsets import UsersViewSet
from crm.models import DealCurrency, DealStage
from notifications.helpers import NotificationsHelper


class UserAccountLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@example.com', 'user@example.com', 'secret')
        self.first_account = Account.objects.create(name='First')
        self.second_account = Account.objects.create(name='Second')

    def test_user_can_only_have_one_link_per_account(self):
        UserAccountLink.objects.create(user=self.user, account=self.first_account)
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserAccountLink.objects.create(user=self.user, account=self.first_account)

    def test_select_replaces_selected_account(self):
        first_link = UserAccountLink.objects.create(user=self.user, account=self.first_account, is_selected=True)
        second_link = UserAccountLink.objects.create(user=self.user, account=self.second_account)

        second_link.select_link()

        first_link.refresh_from_db()
        self.assertFalse(first_link.is_selected)
        self.assertTrue(second_link.is_selected)

    def test_select_replaces_selected_account_when_target_link_was_created_first(self):
        target_link = UserAccountLink.objects.create(user=self.user, account=self.first_account)
        selected_link = UserAccountLink.objects.create(
            user=self.user,
            account=self.second_account,
            is_selected=True,
        )

        target_link.select_link()

        target_link.refresh_from_db()
        selected_link.refresh_from_db()
        self.assertTrue(target_link.is_selected)
        self.assertFalse(selected_link.is_selected)

    def test_manager_gets_selected_link_when_only_user_is_known(self):
        selected_link = UserAccountLink.objects.create(
            user=self.user,
            account=self.first_account,
            is_selected=True,
        )
        UserAccountLink.objects.create(user=self.user, account=self.second_account)

        result = UserAccountLink.objects.get_link_by_user(self.user)

        self.assertEqual(result, selected_link)

    def test_manager_gets_link_for_user_and_account(self):
        UserAccountLink.objects.create(
            user=self.user,
            account=self.first_account,
            is_selected=True,
        )
        second_link = UserAccountLink.objects.create(user=self.user, account=self.second_account)

        result = UserAccountLink.objects.get_link_by_user(self.user, account=self.second_account)

        self.assertEqual(result, second_link)

    def test_select_replaces_archived_selected_link(self):
        archived_link = UserAccountLink.objects.create(
            user=self.user,
            account=self.first_account,
            is_selected=True,
            is_archived=True,
        )
        active_link = UserAccountLink.objects.create(user=self.user, account=self.second_account)

        active_link.select_link()

        archived_link.refresh_from_db()
        active_link.refresh_from_db()
        self.assertFalse(archived_link.is_selected)
        self.assertTrue(active_link.is_selected)

    def test_roles_activity_and_account_permissions(self):
        link = UserAccountLink.objects.create(user=self.user, account=self.first_account, role=UserRole.ADMIN)
        permission = Permission.objects.get(codename='view_deal')
        link.permissions.add(permission)

        self.assertTrue(link.is_admin)
        self.assertTrue(link.has_perm('view_deal'))
        self.assertTrue(link.has_perm(UserPermission.DEAL_VIEW_ALL))

        link.is_active = False
        link.save(update_fields=('is_active',))
        self.assertTrue(link.has_perm('view_deal'))

    def test_serialize_includes_display_name_with_email_fallback(self):
        link = UserAccountLink.objects.create(user=self.user, account=self.first_account)

        self.assertEqual(link.serialize()['name'], 'user@example.com')

    @override_settings(APP_URL='https://crm.example.com/')
    def test_invitation_email_uses_absolute_activation_url(self):
        link = UserAccountLink.objects.create(
            user=self.user,
            account=self.first_account,
            is_active=False,
            is_invited=True,
        )

        with patch.object(link, 'email_user') as email_user:
            NotificationsHelper.user_invite(self.first_account, link)

        context = email_user.call_args.args[1]
        self.assertTrue(context['activation_url'].startswith(
            'https://crm.example.com/activation/'
        ))


class UsersViewSetTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name='permissions_api')
        self.admin = User.objects.create_user('admin@example.com', password='secret')
        self.admin_link = UserAccountLink.objects.create(
            user=self.admin,
            account=self.account,
            role=UserRole.ADMIN,
        )
        manager = User.objects.create_user('manager@example.com', password='secret')
        self.manager_link = UserAccountLink.objects.create(user=manager, account=self.account)
        self.factory = APIRequestFactory()

    def post_permissions(self, permissions):
        request = self.factory.post(
            '/api/users/{}/edit_permissions/'.format(self.manager_link.id),
            {'permissions': permissions},
            format='json',
        )
        request.account = self.account
        request.user_link = self.admin_link
        force_authenticate(request, user=self.admin)
        view = UsersViewSet.as_view({'post': 'edit_permissions'})
        return view(request, pk=self.manager_link.id)

    def test_edit_permissions_saves_custom_permissions(self):
        response = self.post_permissions(['add_company', 'view_all_company'])

        self.assertEqual(response.status_code, 200)
        self.assertSetEqual(
            set(self.manager_link.permissions.values_list('codename', flat=True)),
            {'add_company', 'view_all_company'},
        )

    def test_edit_permissions_rejects_unknown_permissions(self):
        response = self.post_permissions(['is_superuser'])

        self.assertEqual(response.status_code, 400)


class AccountTests(TestCase):
    def test_service_creates_new_user_account_defaults_and_selected_owner(self):
        account = AccountHelper.create('service_acc', email=' owner@example.com ', password='secret')

        owner = account.get_owner()
        self.assertEqual(owner.user.email, 'owner@example.com')
        self.assertTrue(owner.user.check_password('secret'))
        self.assertTrue(owner.is_selected)
        self.assertTrue(Intro.objects.by_account(account).exists())
        self.assertEqual(account.intro.account, account)
        self.assertSetEqual(
            set(DealCurrency.objects.by_account(account).filter(is_enabled=True).values_list('code', flat=True)),
            {'USD', 'EUR'},
        )

    def test_service_creates_additional_account_and_selects_it(self):
        user = User.objects.create_user(
            'existing@example.com',
            'existing@example.com',
            'secret'
        )
        old_account = Account.objects.create(name='old_acc')
        old_link = UserAccountLink.objects.create(user=user, account=old_account, is_selected=True)

        account = AccountHelper.create('new_acc', user=user)

        old_link.refresh_from_db()
        new_link = UserAccountLink.objects.by_account(account).get(user=user)
        self.assertFalse(old_link.is_selected)
        self.assertTrue(new_link.is_selected)
        self.assertEqual(new_link.role, UserRole.OWNER)

    def test_create_owner_initializes_account_atomically(self):
        account = Account.objects.create(name='acme')

        user = AccountHelper.create_owner(account, 'owner@example.com', 'secret')

        link = UserAccountLink.objects.by_account(account).get(user=user)
        self.assertEqual(link.role, UserRole.OWNER)
        self.assertTrue(link.is_selected)
        self.assertEqual(account.get_owner(), link)
        self.assertTrue(Intro.objects.by_account(account).exists())
        self.assertTrue(DealStage.objects.by_account(account).exists())
        self.assertTrue(DealCurrency.objects.by_account(account).exists())

    def test_create_owner_reuses_global_user(self):
        user = User.objects.create_user(
            'existing@example.com',
            'existing@example.com',
            'old-secret'
        )
        account = Account.objects.create(name='additional_acc')

        result = AccountHelper.create_owner(account, 'existing@example.com', 'new-secret')

        self.assertEqual(result, user)
        self.assertTrue(user.check_password('old-secret'))


class AccountSignupTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'owner@example.com',
            'owner@example.com',
            'existing-secret',
        )
        self.first_account = Account.objects.create(name='First account')
        self.first_link = UserAccountLink.objects.create(
            user=self.user,
            account=self.first_account,
            role=UserRole.OWNER,
            is_selected=True,
        )

    def signup(self, password):
        return self.client.post(reverse('login'), {
            'action': 'signup',
            'signup-account_name': 'Second account',
            'signup-email': 'OWNER@example.com',
            'signup-password': password,
        })

    def test_existing_user_can_create_another_account_with_matching_password(self):
        response = self.signup('existing-secret')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertEqual(User.objects.filter(email__iexact='owner@example.com').count(), 1)

        second_account = Account.objects.get(name='Second account')
        second_link = UserAccountLink.objects.get(user=self.user, account=second_account)
        self.first_link.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(second_link.role, UserRole.OWNER)
        self.assertTrue(second_link.is_selected)
        self.assertFalse(self.first_link.is_selected)
        self.assertTrue(self.user.check_password('existing-secret'))

    def test_existing_user_cannot_create_account_with_wrong_password(self):
        response = self.signup('wrong-secret')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email address or password.')
        self.assertFalse(Account.objects.filter(name='Second account').exists())
        self.assertEqual(UserAccountLink.objects.filter(user=self.user).count(), 1)
        self.assertNotIn('_auth_user_id', self.client.session)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@example.com', 'user@example.com', 'secret')
        self.account = Account.objects.create(name='auth_acc')

    def test_login_normalizes_email_and_selects_available_link(self):
        link = UserAccountLink.objects.create(user=self.user, account=self.account)

        result = authenticate(username='  USER@example.com  ', password='secret')

        self.assertEqual(result, self.user)
        link.refresh_from_db()
        self.assertTrue(link.is_selected)

    def test_login_rejects_user_without_active_link(self):
        UserAccountLink.objects.create(user=self.user, account=self.account, is_active=False)
        self.assertIsNone(authenticate(username='user@example.com', password='secret'))

    def test_activation_token_identifies_link(self):
        first_link = UserAccountLink.objects.create(
            user=self.user,
            account=self.account,
            is_active=False,
            is_invited=True
        )
        second_account = Account.objects.create(name='second_auth_acc')
        second_link = UserAccountLink.objects.create(
            user=self.user,
            account=second_account,
            is_active=False,
            is_invited=True
        )
        token = first_link.generate_activation_token()

        self.assertTrue(first_link.check_activation_token(token))
        self.assertFalse(second_link.check_activation_token(token))

    def test_login_uses_another_account_when_one_link_is_inactive(self):
        UserAccountLink.objects.create(
            user=self.user,
            account=self.account,
            is_active=False,
            is_selected=True,
        )
        available_account = Account.objects.create(name='available_auth_acc')
        available_link = UserAccountLink.objects.create(user=self.user, account=available_account)

        result = authenticate(username='user@example.com', password='secret')

        self.assertEqual(result, self.user)
        available_link.refresh_from_db()
        self.assertTrue(available_link.is_selected)

    def test_existing_user_accepts_invite_without_creating_another_user(self):
        link = UserAccountLink.objects.create(
            user=self.user,
            account=self.account,
            is_active=False,
            is_invited=True,
        )
        user_count = User.objects.count()

        response = self.client.post(link.get_activation_url(), {
            'email': self.user.email,
            'first_name': 'Existing',
            'last_name': 'User',
            'password': '',
        })

        link.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), user_count)
        self.assertTrue(link.is_active)
        self.assertFalse(link.is_invited)
        self.assertTrue(link.is_selected)
        self.assertTrue(self.user.check_password('secret'))


class AccountMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user('user@example.com', 'user@example.com', 'secret')
        self.account = Account.objects.create(name='active_acc')

    def request_for_user(self, path='/companies/'):
        request = self.factory.get(path)
        request.user = self.user
        return request

    def test_sets_selected_link_and_account_with_one_joined_query(self):
        link = UserAccountLink.objects.create(
            user=self.user,
            account=self.account,
            is_selected=True,
        )
        request = self.request_for_user()

        response = AccountMiddleware(lambda unused_request: HttpResponse())(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.user_link, link)
        self.assertEqual(request.account, self.account)
        with self.assertNumQueries(0):
            self.assertEqual(request.user_link.account, self.account)

    def test_selects_first_available_link_when_selection_is_missing(self):
        link = UserAccountLink.objects.create(user=self.user, account=self.account)
        request = self.request_for_user()

        response = AccountMiddleware(lambda unused_request: HttpResponse())(request)

        link.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(link.is_selected)
        self.assertEqual(request.user_link, link)

    def test_skips_inactive_links_and_archived_accounts(self):
        UserAccountLink.objects.create(
            user=self.user,
            account=self.account,
            is_selected=True,
            is_active=False,
        )
        archived_account = Account.objects.create(name='archived_acc')
        archived_account.is_archived = True
        archived_account.save(update_fields=('is_archived',))
        UserAccountLink.objects.create(user=self.user, account=archived_account)
        available_account = Account.objects.create(name='available_acc')
        available_link = UserAccountLink.objects.create(user=self.user, account=available_account)
        request = self.request_for_user()

        response = AccountMiddleware(lambda unused_request: HttpResponse())(request)

        available_link.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.account, available_account)
        self.assertTrue(available_link.is_selected)

    def test_leaves_empty_context_without_available_links(self):
        request = self.request_for_user('/rest/deals/')

        response = AccountMiddleware(lambda unused_request: HttpResponse())(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(request.user_link)
        self.assertIsNone(request.account)

    def test_anonymous_request_is_untouched(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/')
        request.user = AnonymousUser()

        response = AccountMiddleware(lambda unused_request: HttpResponse())(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(hasattr(request, 'user_link'))
        self.assertFalse(hasattr(request, 'account'))

    def test_timezone_is_deactivated_after_response(self):
        link = UserAccountLink.objects.create(user=self.user, account=self.account, timezone='Europe/Belgrade')
        request = self.request_for_user()
        request.user_link = link

        middleware = TimezoneMiddleware(lambda unused_request: HttpResponse())
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(timezone.get_current_timezone_name(), 'UTC')


class AccountEndpointsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@example.com', 'user@example.com', 'secret')
        self.first_account = Account.objects.create(name='First account')
        self.second_account = Account.objects.create(name='Second account')
        self.first_link = UserAccountLink.objects.create(
            user=self.user,
            account=self.first_account,
            is_selected=True,
        )
        self.second_link = UserAccountLink.objects.create(user=self.user, account=self.second_account)
        self.client.force_login(self.user)

    def test_lists_only_available_accounts_for_current_user(self):
        other_account = Account.objects.create(name='Other account')
        other_user = User.objects.create_user(
            'other@example.com',
            'other@example.com',
            'secret'
        )
        UserAccountLink.objects.create(user=other_user, account=other_account, is_selected=True)

        response = self.client.get(reverse('account-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual({item['id'] for item in response.json()}, {self.first_account.id, self.second_account.id})

    def test_list_supports_one_two_and_multiple_accounts(self):
        self.assertEqual(len(self.client.get(reverse('account-list')).json()), 2)

        self.second_link.is_active = False
        self.second_link.save(update_fields=('is_active', 'updated_at'))
        self.assertEqual(len(self.client.get(reverse('account-list')).json()), 1)

        self.second_link.is_active = True
        self.second_link.save(update_fields=('is_active', 'updated_at'))
        third_account = Account.objects.create(name='Third account')
        UserAccountLink.objects.create(user=self.user, account=third_account)
        self.assertEqual(len(self.client.get(reverse('account-list')).json()), 3)

    def test_account_endpoints_require_authentication(self):
        self.client.logout()

        self.assertIn(self.client.get(reverse('account-list')).status_code, (401, 403))
        self.assertIn(
            self.client.post(
                reverse('account-switch'),
                {'account_id': self.second_account.id},
                content_type='application/json',
            ).status_code,
            (401, 403),
        )

    def test_list_excludes_inactive_links_and_archived_accounts(self):
        inactive_account = Account.objects.create(name='Inactive account')
        UserAccountLink.objects.create(
            user=self.user,
            account=inactive_account,
            is_active=False,
        )
        archived_account = Account.objects.create(name='Archived account', is_archived=True)
        UserAccountLink.objects.create(user=self.user, account=archived_account)

        response = self.client.get(reverse('account-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item['id'] for item in response.json()},
            {self.first_account.id, self.second_account.id},
        )

    def test_returns_current_account(self):
        response = self.client.get(reverse('account-current'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.first_account.id)
        self.assertTrue(response.json()['is_selected'])
        self.assertTrue(response.json()['is_active'])

    def test_switches_to_an_available_account(self):
        response = self.client.post(
            reverse('account-switch'),
            {'account_id': self.second_account.id},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.first_link.refresh_from_db()
        self.second_link.refresh_from_db()
        self.assertFalse(self.first_link.is_selected)
        self.assertTrue(self.second_link.is_selected)

    def test_cannot_switch_to_another_users_account(self):
        other_account = Account.objects.create(name='Forbidden account')
        other_user = User.objects.create_user(
            'forbidden@example.com',
            'forbidden@example.com',
            'secret'
        )
        UserAccountLink.objects.create(user=other_user, account=other_account, is_selected=True)

        response = self.client.post(
            reverse('account-switch'),
            {'account_id': other_account.id},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        self.first_link.refresh_from_db()
        self.assertTrue(self.first_link.is_selected)

    def test_cannot_switch_to_inactive_or_archived_account(self):
        self.second_link.is_active = False
        self.second_link.save(update_fields=('is_active', 'updated_at'))

        response = self.client.post(
            reverse('account-switch'),
            {'account_id': self.second_account.id},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        self.first_link.refresh_from_db()
        self.assertTrue(self.first_link.is_selected)

        self.second_link.is_active = True
        self.second_link.save(update_fields=('is_active', 'updated_at'))
        self.second_account.is_archived = True
        self.second_account.save(update_fields=('is_archived', 'updated_at'))

        response = self.client.post(
            reverse('account-switch'),
            {'account_id': self.second_account.id},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        self.first_link.refresh_from_db()
        self.assertTrue(self.first_link.is_selected)

    def test_switch_requires_account_id(self):
        response = self.client.post(
            reverse('account-switch'),
            {},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.first_link.refresh_from_db()
        self.assertTrue(self.first_link.is_selected)

    def test_creates_and_selects_additional_account(self):
        response = self.client.post(
            reverse('account-create'),
            {'name': 'New account'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        account = Account.objects.get(pk=response.json()['id'])
        link = UserAccountLink.objects.by_account(account).get(user=self.user)
        self.first_link.refresh_from_db()
        self.assertTrue(link.is_selected)
        self.assertFalse(self.first_link.is_selected)
        self.assertTrue(Intro.objects.by_account(account).exists())

    def test_profile_timezone_is_saved_on_current_link(self):
        response = self.client.post(
            '/rest/edit_profile/',
            {
                'email': 'updated@example.com',
                'first_name': 'Updated',
                'last_name': 'User',
                'timezone': 'Europe/Belgrade',
                'language': 'ru',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.first_link.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(str(self.first_link.timezone), 'Europe/Belgrade')
        self.assertEqual(self.first_link.language, 'ru')
        self.assertEqual(str(self.second_link.timezone), 'UTC')
        self.assertEqual(self.second_link.language, 'en')
        self.assertEqual(response.json()['first_name'], 'Updated')
        self.assertEqual(response.json()['last_name'], 'User')
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, 'ru')
