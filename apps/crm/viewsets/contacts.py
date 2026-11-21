import logging
import openpyxl
import unicodecsv as csv

from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File
from django.db.models import Q
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _, gettext_noop, ngettext, override

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from crm.const import ItemType
from crm.filters import CompanyFilterSet, PersonFilterSet
from crm.forms import CompanyForm, PersonForm
from crm.mixins import ErrorResponseMixin, EditMTMFieldsMixin
from crm.models import Activity, Company, Person, Tag, ContactsImport, ExtraField, ItemResponsibleLink
from crm.tasks import notify_responsibles, import_contacts
from crm.viewsets.base import ItemViewSet
from crm.utils import save_contacts_import_data


__all__ = (
    'CompaniesViewSet',
    'PersonsViewSet',
    'ContactsImportsViewSet',
)


class CompaniesViewSet(ItemViewSet):
    model = Company
    filterset_class = CompanyFilterSet
    ordering_fields = (
        'name', 'address', 'website', 'tags', 'details', 'user', 'created_at',
    )
    search_fields = ('name', 'address', 'website', 'phones', 'emails', 'details',)

    def get_queryset(self):
        user = self.request.user

        companies_qs = Company.objects.by_account(self.request.account).select_related('user').only(
            'id', 'name',  'address', 'website', 'phones', 'emails', 'details', 'created_at',
            'user_id', 'user__email', 'user__first_name', 'user__last_name'
        )

        if not self.request.user_link.has_perm('view_all_company'):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(self.request.account).filter(
                item_type=ItemType.COMPANY.value,
                user_id=user.id
            ).values('item_id')
            companies_qs = companies_qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        return companies_qs

    @action(detail=False, methods=['post'])
    def add(self, request):
        form = CompanyForm(data=request.data, account=request.account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        company = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.COMPANY.value, [company.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.COMPANY.value, [company.id], [tag.id for tag in tags], 'set')

        notify_responsibles.delay(request.account.id, ItemType.COMPANY.value, company.id, [], request.user_link.name)

        Activity.log_addition(company)

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.COMPANY.value, [company.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.COMPANY.value, [company.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.COMPANY.value, [company.id]),
        }

        return Response({
            'company': company.serialize(**serialize_params),
        })

    @action(detail=True, methods=['post'])
    def edit(self, request, pk):
        try:
            company = Company.objects.by_account(request.account).get(id=pk)
        except Company.DoesNotExist:
            return Response({'error': _('This company does not exist')}, status=400)

        old_responsible_ids = company.get_responsible_ids()

        form = CompanyForm(data=request.data, instance=company, account=request.account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        company = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.COMPANY.value, [company.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.COMPANY.value, [company.id], [tag.id for tag in tags], 'set')

        notify_responsibles.delay(
            request.account.id, ItemType.COMPANY.value, company.id, old_responsible_ids, request.user_link.name
        )

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.COMPANY.value, [company.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.COMPANY.value, [company.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.COMPANY.value, [company.id]),
        }

        return Response({
            'company': company.serialize(**serialize_params),
        })


class PersonsViewSet(ItemViewSet):
    model = Person
    filterset_class = PersonFilterSet
    ordering_fields = (
        'name', 'company__name', 'post', 'phones', 'emails', 'tags', 'details', 'user', 'created_at',
    )
    search_fields = ('name', 'company__name', 'post', 'phones', 'emails', 'details',)

    def get_queryset(self):
        user = self.request.user

        persons_qs = Person.objects.by_account(self.request.account).select_related(
            'company', 'user'
        ).only(
            'id', 'name',  'post', 'phones', 'emails', 'details', 'created_at',
            'company_id', 'company__name', 'company__phones', 'company__emails',
            'user_id', 'user__email', 'user__first_name', 'user__last_name'
        )

        if not self.request.user_link.has_perm('view_all_person'):
            responsible_links_qs = ItemResponsibleLink.objects.by_account(self.request.account).filter(
                item_type=ItemType.PERSON.value,
                user_id=user.id
            ).values('item_id')
            persons_qs = persons_qs.filter(Q(id__in=responsible_links_qs) | Q(user_id=user.id)).distinct()

        return persons_qs

    @action(detail=False, methods=['post'])
    def add(self, request):
        form = PersonForm(data=request.data, account=request.account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        person = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.PERSON.value, [person.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.PERSON.value, [person.id], [tag.id for tag in tags], 'set')

        notify_responsibles.delay(request.account.id, ItemType.PERSON.value, person.id, [], request.user_link.name)

        Activity.log_addition(person)

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.PERSON.value, [person.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.PERSON.value, [person.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.PERSON.value, [person.id]),
        }

        return Response({
            'person': person.serialize(**serialize_params),
        })

    @action(detail=True, methods=['post'])
    def edit(self, request, pk):
        try:
            person = Person.objects.by_account(request.account).get(id=pk)
        except Person.DoesNotExist:
            return Response({'error': _('This contact does not exist')}, status=400)

        old_responsible_ids = person.get_responsible_ids()

        form = PersonForm(data=request.data, instance=person, account=request.account, user=request.user)
        if not form.is_valid():
            return Response({
                'errors': form.errors
            }, status=400)

        person = form.save()

        responsibles = form.cleaned_data.get('responsibles', [])
        self.update_items_responsibles(
            ItemType.PERSON.value, [person.id], [responsible.id for responsible in responsibles], 'set'
        )
        tags = form.cleaned_data.get('tags', [])
        self.update_items_tags(ItemType.PERSON.value, [person.id], [tag.id for tag in tags], 'set')

        notify_responsibles.delay(
            request.account.id, ItemType.PERSON.value, person.id, old_responsible_ids, request.user_link.name
        )

        serialize_params = {
            'request': request,
            'responsible_links_map': self.get_responsible_links_map(ItemType.PERSON.value, [person.id]),
            'tag_links_map': self.get_tag_links_map(ItemType.PERSON.value, [person.id]),
            'extra_field_links_map': self.get_extra_field_links_map(ItemType.PERSON.value, [person.id]),
        }

        return Response({
            'person': person.serialize(**serialize_params),
        })


class ContactsImportsViewSet(ErrorResponseMixin, EditMTMFieldsMixin, GenericViewSet):
    CSV = 'csv'
    XLS = 'xls'

    EXTENSIONS = (CSV, XLS)

    FIELDS_MAP = {
        'company_name': (gettext_noop('company'), gettext_noop('name'), gettext_noop('company name')),
        'address': (gettext_noop('address'), gettext_noop('company address')),
        'website': (gettext_noop('website'), gettext_noop('company website')),
        'person_name': (
            gettext_noop('full name'), gettext_noop('first name last name'), gettext_noop('last name first name'),
        ),
        'post': (gettext_noop('job title'),),
        'phones': (gettext_noop('phone'), gettext_noop('phones')),
        'emails': (gettext_noop('email address'), gettext_noop('email'), gettext_noop('e-mail')),
        'details': (gettext_noop('additional information'), gettext_noop('additional info')),
    }

    RESPONSIBLES_NAMES = (gettext_noop('Assignees'),)
    TAGS_NAMES = (gettext_noop('Tags'),)

    @staticmethod
    def _localized_names(values):
        names = {str(value).strip().lower() for value in values}
        for language_code, language_name in settings.LANGUAGES:
            with override(language_code):
                names.update(str(_(value)).strip().lower() for value in values)
        return names

    def _get_field_from_name(self, name):
        for field, values in self.FIELDS_MAP.items():
            if name.strip().lower() in self._localized_names(values):
                return field
        return ''

    @staticmethod
    def _name_matches(name, values):
        return name.strip().lower() in ContactsImportsViewSet._localized_names(values)

    def list(self, request):
        contacts_imports = ContactsImport.objects.by_account(request.account).filter(is_completed=True)
        data = [contacts_import.serialize() for contacts_import in self.paginate_queryset(contacts_imports)]
        return self.get_paginated_response(data)

    def create(self, request):
        data = request.data

        contacts_file = data.get('file')
        if not contacts_file or not isinstance(contacts_file, File):
            return self.get_error_response(_('You did not select a file to import'))

        has_header = True if data['has_header'] == 'true' else False
        merge_contacts = True if data['merge_contacts'] == 'true' else False
        company_merge_field = data.get('company_merge_field', '')
        person_merge_field = data.get('person_merge_field', '')

        extension = contacts_file.name.split('.')[-1]
        if extension not in self.EXTENSIONS:
            return self.get_error_response(_('The file must have one of these extensions: .csv, .xls'))

        if extension == self.CSV:
            try:
                reader = csv.reader(contacts_file, dialect='excel', delimiter=str(','))
                rows = [r for r in reader if ''.join(r).strip()]
            except UnicodeDecodeError as e:
                logging.error('ContactsImportsAPI.create: UnicodeDecodeError - {}'.format(smart_str(e)))
                return self.get_error_response(_('Unsupported file encoding'))
            except Exception as e:
                logging.error('ContactsImportsAPI.create: unknown error - {}'.format(smart_str(e)))
                return self.get_error_response(_('Error reading the file'))
        elif extension == self.XLS:
            try:
                workbook = openpyxl.load_workbook(contacts_file, data_only=True)
                sheet = workbook.active
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    rows.append(list(row))
            except UnicodeDecodeError as e:
                logging.error('ContactsImportsAPI.create: UnicodeDecodeError - {}'.format(smart_str(e)))
                return self.get_error_response(_('Unsupported file encoding'))
            except Exception as e:
                logging.error('ContactsImportsAPI.create: openpyxl error - {}'.format(smart_str(e)))
                return self.get_error_response(_('Error reading the file'))
        else:
            rows = []

        header_row = None
        if has_header and len(rows):
            header_row = list(map(str, rows.pop(0)))

        rows_cnt = len(rows)
        if not rows_cnt:
            return self.get_error_response(_('The file contains no data'))

        duplicates_cnt = 0
        unique_rows = []
        for row in rows:
            if row in unique_rows:
                duplicates_cnt += 1
                continue

            unique_rows.append(row)

        contacts_import = ContactsImport.objects.create(
            account=request.account,
            user_id=request.user.id,
            name=contacts_file.name,
            file=contacts_file,
            rows_cnt=rows_cnt,
            duplicates_cnt=duplicates_cnt,
            persons_cnt=0,
            companies_cnt=0,
            merge_contacts=merge_contacts,
            company_merge_field=company_merge_field,
            person_merge_field=person_merge_field
        )

        save_contacts_import_data(request.account.id, contacts_import.id, unique_rows)

        if has_header:
            fields_map = {}
            mapped_headers = [self._get_field_from_name(fieldname) for fieldname in header_row]
            link_prefix = 'person' if 'person_name' in mapped_headers else 'company'
            extra_fields = {
                field.name.strip().lower(): field.codename
                for field in ExtraField.objects.by_account(request.account)
            }
            for index, fieldname in enumerate(header_row):
                field = mapped_headers[index]
                if not field and self._name_matches(fieldname, self.RESPONSIBLES_NAMES):
                    field = '{}_responsibles'.format(link_prefix)
                elif not field and self._name_matches(fieldname, self.TAGS_NAMES):
                    field = '{}_tags'.format(link_prefix)
                elif not field:
                    field = extra_fields.get(fieldname.strip().lower(), '')
                fields_map['field_{}'.format(index)] = field
        else:
            fields_map = {'field_{}'.format(index): '' for index, field in enumerate(unique_rows[0])}

        return Response(data={
            'rows_cnt': rows_cnt,
            'fields_map': fields_map,
            'header_row': header_row,
            'sample_rows': unique_rows[:3],
            'contacts_import_id': contacts_import.id,
            'duplicates_cnt': duplicates_cnt,
        })

    @action(detail=True, methods=['post'])
    def start_import(self, request, pk):
        error = _('Could not start the import. Try importing the file again.')

        fields_map = request.data.get('fields_map')
        if not fields_map:
            return self.get_error_response(error)

        try:
            contacts_import = ContactsImport.objects.by_account(request.account).get(id=pk)
        except ContactsImport.DoesNotExist:
            return self.get_error_response(error)

        contacts_import.fields_map = fields_map
        contacts_import.save(update_fields=('fields_map',))

        import_contacts.delay(request.account.id, contacts_import.id)
        return Response({})

    def retrieve(self, request, pk):
        try:
            contacts_import = ContactsImport.objects.by_account(request.account).get(id=pk)
        except ContactsImport.DoesNotExist:
            return self.get_error_response(_('Import failed. Try importing the file again.'))

        if not contacts_import.is_completed:
            return Response({
                'is_completed': False,
            })

        msg = _('Contact import completed successfully. ')

        companies_cnt = contacts_import.companies_cnt
        persons_cnt = contacts_import.persons_cnt
        if companies_cnt and persons_cnt:
            companies = ngettext('%(count)d company', '%(count)d companies', companies_cnt) % {'count': companies_cnt}
            persons = ngettext('%(count)d contact', '%(count)d contacts', persons_cnt) % {'count': persons_cnt}
            msg += _('Imported {companies} and {contacts}.').format(companies=companies, contacts=persons)
        elif companies_cnt:
            msg += ngettext('Imported %(count)d company.', 'Imported %(count)d companies.', companies_cnt) % {
                'count': companies_cnt,
            }
        elif persons_cnt:
            msg += ngettext('Imported %(count)d contact.', 'Imported %(count)d contacts.', persons_cnt) % {
                'count': persons_cnt,
            }
        else:
            msg = _('No contacts were imported.')

        intro = request.account.intro
        if not intro.is_completed:
            intro.complete()

        return Response({
            'is_completed': True,
            'msg': msg,
        })

    @action(detail=True, methods=['post'])
    def batch_edit_responsibles(self, request, pk):
        data = request.data

        try:
            contacts_import = ContactsImport.objects.by_account(request.account).get(id=pk)
        except ContactsImport.DoesNotExist:
            return self.get_error_response(_('Could not edit assignees. Please refresh the page.'))

        action = data.get('action')
        if not action:
            return self.get_error_response(_('No action selected.'))

        companies = Company.objects.filter(contacts_import=contacts_import) if contacts_import.companies_cnt else []
        persons = Person.objects.filter(contacts_import=contacts_import) if contacts_import.persons_cnt else []

        responsibles = data.get('responsibles') or []
        responsibles = User.objects.filter(
            useraccountlink__account=request.account,
            useraccountlink__is_active=True,
            id__in=responsibles,
        ).distinct()

        for company in companies:
            self.update_items_responsibles(
                Company.ITEM_TYPE, [company.id],
                [responsible.id for responsible in responsibles], action
            )

        for person in persons:
            self.update_items_responsibles(
                Person.ITEM_TYPE, [person.id],
                [responsible.id for responsible in responsibles], action
            )

        return Response({})

    @action(detail=True, methods=['post'])
    def batch_edit_tags(self, request, pk):
        data = request.data

        try:
            contacts_import = ContactsImport.objects.by_account(request.account).get(id=pk)
        except ContactsImport.DoesNotExist:
            return self.get_error_response(_('Could not edit tags. Please refresh the page.'))

        action = data.get('action')
        if not action:
            return self.get_error_response(_('No action selected.'))

        companies = Company.objects.filter(contacts_import=contacts_import) if contacts_import.companies_cnt else []
        persons = Person.objects.filter(contacts_import=contacts_import) if contacts_import.persons_cnt else []

        tags = data.get('tags') or []
        tags = [Tag.objects.get_or_create(account=request.account, name=tag)[0] for tag in tags if isinstance(tag, str)]

        for company in companies:
            self.update_items_tags(Company.ITEM_TYPE, [company.id], [tag.id for tag in tags], action)

        for person in persons:
            self.update_items_tags(Person.ITEM_TYPE, [person.id], [tag.id for tag in tags], action)

        return Response({})
