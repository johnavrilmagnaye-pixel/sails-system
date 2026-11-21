from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.conf import settings
from django.urls import reverse
from rest_framework.exceptions import ValidationError as DRFValidationError

from accounts.models import Account, Intro, UserAccountLink
from crm.const import ItemType
from crm.filters.base import parse_date_range
from crm.mixins import EditMTMFieldsMixin
from crm.models import Company, ContactsImport, Deal, DealCurrency, ItemResponsibleLink, ItemTagLink, Tag
from crm.tasks import import_contacts
from crm.utils import save_contacts_import_data
from crm.viewsets.base import ItemViewSet
from crm.viewsets.contacts import ContactsImportsViewSet


class EditResponsiblesTests(TestCase):
    def test_returns_account_display_name_for_django_user(self):
        account = Account.objects.create(name='responsibles_account')
        user = User.objects.create_user(
            'assignee@example.com',
            first_name='Jane',
            last_name='Doe',
        )
        UserAccountLink.objects.create(account=account, user=user)
        request = self.client.post('/rest/deals/7/edit_responsibles/', {'value[]': [user.id]}).wsgi_request
        request.account = account
        request.user_link = SimpleNamespace(name='Assigning User')
        item = SimpleNamespace(
            id=7,
            ITEM_TYPE=ItemType.DEAL.value,
            get_responsible_ids=lambda: [],
        )
        viewset = ItemViewSet()
        viewset.get_object = Mock(return_value=item)
        viewset.update_items_responsibles = Mock()

        with patch('crm.viewsets.base.notify_responsibles.delay'):
            response = viewset.edit_responsibles(request, pk=item.id)

        self.assertEqual(response.data, {
            'success': True,
            'responsibles': [{'id': user.id, 'name': 'Jane Doe'}],
        })


class ContactsImportFieldMappingTests(TestCase):
    def test_matches_english_and_russian_headers_regardless_of_active_language(self):
        viewset = ContactsImportsViewSet()

        with self.settings(LANGUAGE_CODE='en'):
            self.assertEqual(viewset._get_field_from_name('Company name'), 'company_name')
            self.assertEqual(viewset._get_field_from_name('Название'), 'company_name')
            self.assertEqual(viewset._get_field_from_name('Full name'), 'person_name')
            self.assertEqual(viewset._get_field_from_name('ФИО'), 'person_name')
            self.assertTrue(viewset._name_matches('Assignees', viewset.RESPONSIBLES_NAMES))
            self.assertTrue(viewset._name_matches('Ответственные', viewset.RESPONSIBLES_NAMES))
            self.assertTrue(viewset._name_matches('Tags', viewset.TAGS_NAMES))
            self.assertTrue(viewset._name_matches('Теги', viewset.TAGS_NAMES))

    def test_intro_mapping_options_include_responsibles_tags_and_plural_contact_fields(self):
        source = (
            Path(__file__).resolve().parent
            / 'static/crm/js/views/intro/IntroImportStep2View.js'
        ).read_text()

        for field in (
            'company_responsibles', 'company_tags',
            'person_responsibles', 'person_tags',
            'phones', 'emails',
        ):
            self.assertIn("value: '{}'".format(field), source)

        self.assertNotIn("value: 'phone'", source)
        self.assertNotIn("value: 'email'", source)

    def test_user_facing_javascript_strings_do_not_use_responsibles(self):
        templates_dir = Path(__file__).resolve().parent / 'templates/crm/js_templates'
        user_facing_sources = '\n'.join(
            path.read_text() for path in templates_dir.glob('*.html')
        )

        self.assertNotIn("gettext('Assign responsibles", user_facing_sources)
        self.assertIn("gettext('Manage assignees')", user_facing_sources)
        self.assertIn("gettext('Manage assignees for')", user_facing_sources)

    def test_imported_company_is_created_in_import_account(self):
        user = User.objects.create_user('import@example.com')
        account = Account.objects.create(name='import_account')
        UserAccountLink.objects.create(user=user, account=account, is_selected=True)
        contacts_import = ContactsImport.objects.create(
            account=account,
            user=user,
            name='companies.csv',
            file=SimpleUploadedFile('companies.csv', b'Company name\nAcme'),
            fields_map={'field_0': 'company_name', 'field_1': 'company_tags'},
            rows_cnt=1,
            duplicates_cnt=0,
            persons_cnt=0,
            companies_cnt=0,
            merge_contacts=False,
        )
        save_contacts_import_data(account.id, contacts_import.id, [['Acme', 'customer, important']])

        import_contacts(account.id, contacts_import.id)

        company = Company.objects.get(name='Acme')
        self.assertEqual(company.account_id, account.id)
        self.assertEqual(
            set(company.get_tag_links().values_list('tag__name', flat=True)),
            {'customer', 'important'},
        )


class DateRangeParsingTests(TestCase):
    def test_parses_localized_date_range(self):
        start, end = parse_date_range('23.07.2026 - 21.08.2026')

        self.assertEqual(start.date().isoformat(), '2026-07-23')
        self.assertEqual(end.date().isoformat(), '2026-08-22')

    def test_parses_iso_date_range_without_splitting_date_hyphens(self):
        start, end = parse_date_range('2026-07-23 - 2026-08-21')

        self.assertEqual(start.date().isoformat(), '2026-07-23')
        self.assertEqual(end.date().isoformat(), '2026-08-22')


class FrontendLocalizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('i18n@example.com', password='secret')
        self.account = Account.objects.create(name='i18n_account')
        Intro.objects.create(account=self.account, is_completed=True)
        UserAccountLink.objects.create(
            user=self.user,
            account=self.account,
            is_selected=True,
        )
        self.client.force_login(self.user)

    def test_shell_exposes_worldwide_timezone_options(self):
        response = self.client.get(reverse('companies'))

        self.assertContains(response, 'id="timezone-options"')
        self.assertContains(response, 'America/New_York')
        self.assertContains(response, 'Asia/Tokyo')
        self.assertContains(response, 'Europe/Belgrade')

    def test_account_switcher_is_outside_edit_profile_form(self):
        source = (
            Path(__file__).resolve().parent
            / 'templates/crm/js_templates/settings_templates.html'
        ).read_text()
        edit_profile_template = source.split(
            'id="edit-profile-form-tmpl"', 1
        )[1].split('</script>', 1)[0]
        profile_layout_template = source.split(
            'id="settings-profile-layout-tmpl"', 1
        )[1].split('</script>', 1)[0]

        self.assertNotIn('name="account"', edit_profile_template)
        self.assertIn('class="form-horizontal account-switcher"', profile_layout_template)
        self.assertIn('name="account" v-select2="$root.selectedAccountId"', profile_layout_template)

        view_source = (
            Path(__file__).resolve().parent
            / 'static/crm/js/views/settings/SettingsProfileLayoutView.js'
        ).read_text()
        self.assertIn("'change.settings-profile-account'", view_source)
        self.assertIn('self.$root.switchAccount(accountId)', view_source)

    def test_language_switch_translates_templates_and_javascript_catalog(self):
        response = self.client.post(reverse('set_language'), {
            'language': 'ru',
            'next': reverse('companies'),
        })

        self.assertRedirects(response, reverse('companies'), fetch_redirect_response=False)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, 'ru')
        self.assertEqual(UserAccountLink.objects.get(user=self.user, account=self.account).language, 'ru')
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'ru'

        shell = self.client.get(reverse('companies'))
        self.assertContains(shell, 'Компании')
        catalog = self.client.get(reverse('javascript-catalog')).content.decode('utf-8')
        self.assertIn('"Loading..."', catalog)
        self.assertIn(r'\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430...', catalog)


class FrontendComponentModernizationTests(TestCase):
    def test_shell_registers_shared_components_and_accessible_live_regions(self):
        source = Path('apps/crm/templates/crm/app.html').read_text()

        self.assertIn("core/js/views/Components.js", source)
        self.assertIn('aria-live="polite"', source)
        self.assertIn('aria-controls="app-content"', source)
        self.assertIn('@click="toggleSidebar"', source)

    def test_route_templates_use_shared_loading_state(self):
        template_dir = Path('apps/crm/templates/crm/js_templates')
        route_templates = list(template_dir.glob('*_templates.html'))
        source = '\n'.join(path.read_text() for path in route_templates)

        self.assertIn('<ui-state v-if="$loadingRouteData"', source)
        self.assertNotIn('v-if="$loadingRouteData" class="loading"', source)

    def test_modals_and_pagination_have_keyboard_semantics(self):
        modal_view = Path('apps/core/static/core/js/views/ModalView.js').read_text()
        pagination = Path('apps/core/templates/core/js_templates/grid_templates.html').read_text()

        self.assertIn("event.keyCode !== 9", modal_view)
        self.assertIn("previouslyFocusedElement.focus()", modal_view)
        self.assertIn('aria-current="page"', pagination)
        self.assertIn(':aria-disabled=', pagination)

class CrossAccountLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@example.com', password='secret')
        self.other_user = User.objects.create_user('other@example.com', password='secret')
        self.account = Account.objects.create(name='links_a')
        self.other_account = Account.objects.create(name='links_b')
        UserAccountLink.objects.create(user=self.user, account=self.account)
        UserAccountLink.objects.create(user=self.other_user, account=self.other_account)
        self.company = Company.objects.create(account=self.account, user=self.user, name='Company A')
        self.other_company = Company.objects.create(
            account=self.other_account, user=self.other_user, name='Company B'
        )
        self.tag = Tag.objects.create(account=self.account, name='Tag A')
        self.other_tag = Tag.objects.create(account=self.other_account, name='Tag B')

    def test_responsible_link_rejects_user_from_another_account(self):
        link = ItemResponsibleLink(
            account=self.account,
            item_type=ItemType.COMPANY.value,
            item_id=self.company.id,
            user=self.other_user,
        )

        with self.assertRaises(DjangoValidationError):
            link.save()

    def test_tag_link_rejects_item_and_tag_from_other_accounts(self):
        with self.assertRaises(DjangoValidationError):
            ItemTagLink.objects.create(
                account=self.account,
                item_type=ItemType.COMPANY.value,
                item_id=self.other_company.id,
                tag=self.tag,
            )

        with self.assertRaises(DjangoValidationError):
            ItemTagLink.objects.create(
                account=self.account,
                item_type=ItemType.COMPANY.value,
                item_id=self.company.id,
                tag=self.other_tag,
            )

    def test_bulk_link_update_rejects_foreign_ids_before_writing(self):
        mixin = EditMTMFieldsMixin()
        mixin.request = SimpleNamespace(account=self.account)

        with self.assertRaises(DRFValidationError):
            mixin.update_items_tags(
                ItemType.COMPANY.value, [self.company.id], [self.other_tag.id], mixin.ACTION_SET
            )
        with self.assertRaises(DRFValidationError):
            mixin.update_items_responsibles(
                ItemType.COMPANY.value, [self.other_company.id], [self.user.id], mixin.ACTION_SET
            )

        self.assertFalse(ItemTagLink.objects.exists())
        self.assertFalse(ItemResponsibleLink.objects.exists())

    def test_responsible_lookup_does_not_silently_drop_foreign_users(self):
        with self.assertRaises(DRFValidationError):
            ItemViewSet._get_account_responsibles(self.account, [self.user.id, self.other_user.id])


class DealSerializationTests(TestCase):
    def test_info_serializes_active_responsible_link(self):
        user = User.objects.create_user('responsible@example.com')
        account = Account.objects.create(name='deals')
        UserAccountLink.objects.create(user=user, account=account)
        currency = DealCurrency.objects.create(account=account, name='USD', code='USD', format='$%s')
        deal = Deal.objects.create(account=account, user=user, name='Deal', currency=currency)
        responsible_link = ItemResponsibleLink.objects.create(
            account=account,
            item_type=ItemType.DEAL.value,
            item_id=deal.id,
            user=user,
        )

        serialized = deal.serialize(responsible_links_map={deal.id: [responsible_link]})

        self.assertIn('<b>Assignees:</b>', serialized['info'])
        self.assertIn(user.email, serialized['info'])
