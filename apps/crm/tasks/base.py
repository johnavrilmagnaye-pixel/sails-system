import datetime as dt
import unicodecsv
import openpyxl
from celery.utils.log import get_task_logger
from io import BytesIO

from django.apps import apps
from django.db import transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils import formats, timezone as tz
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from core.utils import iter_chunks
from project.celery import app

from accounts.models import Account, UserAccountLink, get_user_account_name
from crm.helpers import ItemsHelper
from crm.models import (
    Task, ContactsImport, Company, Person, Tag, ExtraField, Activity, ItemsExport, Deal,
    MODEL_PLURALS, PeriodicTask, Upload, Note, RemindTaskLink,
    ItemTagLink, ItemResponsibleLink, ItemExtraFieldLink, ItemType,
)
from crm.utils import get_contacts_import_data
from notifications.helpers import NotificationsHelper


logger = get_task_logger(__name__)


__all__ = (
    'notify_responsibles',
    'set_remind_task_links',
    'remind_tasks',
    'send_tasks_digest',
    'import_contacts',
    'export_items',
    'archive_items',
    'update_tasks_state',
    'create_periodic_tasks',
    'clean_archived_items',
)


COMMON_FIELDS = ('phones', 'emails', 'details')
COMPANY_FIELDS = ('address', 'website')
PERSON_FIELDS = ('post',)


@app.task(name='crm.notify_responsibles')
def notify_responsibles(account_id, item_type, item_id, old_responsible_ids, assigned_by_name):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        return

    item = ItemsHelper.fetch_item(account, item_type, item_id)
    if not item or item.account_id != account.id:
        return

    responsible_ids = set(item.get_responsible_ids()) - {item.user_id}
    if old_responsible_ids:
        responsible_ids -= set(old_responsible_ids)

    for user_link in UserAccountLink.objects.active().by_account(account).filter(
        user_id__in=responsible_ids
    ).select_related('user'):
        NotificationsHelper.responsible_assigned(account, user_link, item, assigned_by_name)


@app.task(name='crm.set_remind_task_links')
def set_remind_task_links(account_id, task_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        return

    try:
        task = Task.objects.by_account(account).get(id=task_id)
    except Task.DoesNotExist:
        return

    if not task.expire_date:
        task.remindtasklink_set.filter(is_active=True).update(is_active=False)
        return

    responsible_ids = task.get_responsible_ids()
    for responsible_id in responsible_ids:
        remind_link, _created = task.remindtasklink_set.get_or_create(
            account=account,
            responsible_id=responsible_id,
        )
        remind_link.is_reminded = False
        remind_link.is_active = True
        remind_link.save(update_fields=('is_reminded', 'is_active'))

    task.remindtasklink_set.filter(is_active=True).exclude(
        responsible_id__in=responsible_ids,
    ).update(is_active=False)


@app.task(name='crm.remind_tasks')
def remind_tasks(account_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        return

    active_user_links = UserAccountLink.objects.active().by_account(account).select_related('user')
    for user_link in active_user_links:
        remind_time = tz.now() + user_link.notification_settings.remind_task_before
        remind_links = RemindTaskLink.objects.by_account(account).filter(
            responsible_id=user_link.user_id,
            is_active=True,
            is_reminded=False,
            task__state=Task.STATE_PENDING,
            task__expire_date__lte=remind_time
        ).select_related('task')
        for remind_link in remind_links:
            NotificationsHelper.task_reminder(account, user_link, remind_link.task)

        remind_links.update(is_reminded=True)

    logger.info(f'remind_tasks completed for {account.name=} {account.id=})')


@app.task(name='crm.send_tasks_digest')
def send_tasks_digest(account_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        return

    active_user_links = UserAccountLink.objects.active().by_account(account).select_related('user')
    for user_link in active_user_links:
        now = tz.now().astimezone(user_link.timezone)
        if now.hour != 10 or now.minute != 0:
            continue

        remind_links = RemindTaskLink.objects.by_account(account).select_related('task').filter(
            responsible_id=user_link.user_id,
            is_active=True,
            task__state__in=(Task.STATE_PENDING, Task.STATE_OVERDUE),
            task__expire_date__lt=(now + dt.timedelta(days=1)).replace(hour=0, minute=0)
        )
        if not remind_links:
            continue

        NotificationsHelper.tasks_digest(
            account,
            user_link,
            [remind_link.task for remind_link in remind_links],
        )


@app.task(name='crm.import_contacts')
def import_contacts(account_id, contacts_import_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        logger.warning('import_contacts failed: account does not exist (id={})'.format(account_id))
        return

    try:
        contacts_import = ContactsImport.objects.by_account(account).get(id=contacts_import_id)
    except ContactsImport.DoesNotExist:
        return

    contacts_data = get_contacts_import_data(account_id, contacts_import_id)
    if not contacts_data:
        contacts_import.archive()
        return

    rows = []
    for row in contacts_data:
        dict_row = {}
        for index, value in enumerate(row):
            dict_row[contacts_import.fields_map['field_{}'.format(index)]] = value
        rows.append(dict_row)

    companies_cnt = 0
    persons_cnt = 0

    merge_contacts = contacts_import.merge_contacts
    company_merge_field = contacts_import.company_merge_field
    person_merge_field = contacts_import.person_merge_field

    def _set_item_fields(item, row, fields):
        for field_name in fields:
            field_value = row.get(field_name)
            if not field_value:
                continue
            if field_name == 'phones' and isinstance(field_value, float):
                field_value = str(int(field_value))
            elif field_name == 'website' and not field_value.startswith('http'):
                field_value = 'http://{}'.format(field_value)

            if field_name in ('phones', 'emails'):
                field_value = _split_list(field_value)

            setattr(item, field_name, field_value)

    def _split_list(value):
        if not value:
            return []
        return [part.strip() for part in str(value).replace('\n', ',').split(',') if part.strip()]

    def _set_item_links(item, row, prefix):
        responsible_names = _split_list(row.get('{}_responsibles'.format(prefix)))
        if responsible_names:
            responsible_ids = []
            for user_link in UserAccountLink.objects.active().by_account(account).select_related('user'):
                names = {user_link.user.email, user_link.name}
                if any(name and name.casefold() in {value.casefold() for value in names if value} for name in responsible_names):
                    responsible_ids.append(user_link.user_id)
            ItemResponsibleLink.objects.filter(
                account=account, item_type=item.ITEM_TYPE, item_id=item.id
            ).delete()
            ItemResponsibleLink.objects.bulk_create([
                ItemResponsibleLink(account=account, item_type=item.ITEM_TYPE, item_id=item.id, user_id=user_id)
                for user_id in responsible_ids
            ], ignore_conflicts=True)

        tag_names = _split_list(row.get('{}_tags'.format(prefix)))
        if tag_names:
            tags = [Tag.objects.get_or_create(account=account, name=name)[0] for name in tag_names]
            ItemTagLink.objects.filter(account=account, item_type=item.ITEM_TYPE, item_id=item.id).delete()
            ItemTagLink.objects.bulk_create([
                ItemTagLink(account=account, item_type=item.ITEM_TYPE, item_id=item.id, tag=tag)
                for tag in tags
            ], ignore_conflicts=True)

    rows_cnt = len(rows)
    for index, row in enumerate(rows):
        company_name = row.get('company_name')
        if company_name:
            try:
                with transaction.atomic():
                    is_new = True
                    if merge_contacts:
                        if 'extra_field' in company_merge_field:
                            merge_field_value = row.get(company_merge_field)
                            lookup = {
                                'field_id': company_merge_field[12:],
                                'value': merge_field_value,
                            }
                            if merge_field_value and ItemExtraFieldLink.objects.by_account(account).filter(item_type=ItemType.COMPANY.value, **lookup).exists():
                                extra_field_value = ItemExtraFieldLink.objects.by_account(account).filter(item_type=ItemType.COMPANY.value, **lookup).last()
                                company = extra_field_value.item
                                is_new = False
                        else:
                            merge_field_value = row.get('company_name' if company_merge_field == 'name' else company_merge_field)
                            lookup = {'{}__iexact'.format(company_merge_field): merge_field_value}
                            if merge_field_value and Company.objects.by_account(account).filter(**lookup).exists():
                                company = Company.objects.select_for_update().by_account(account).filter(**lookup).last()
                                is_new = False

                    if is_new:
                        company = Company(account=account, name=company_name, user=contacts_import.user)

                    _set_item_fields(company, row, COMMON_FIELDS + COMPANY_FIELDS)

                    try:
                        company.clean_fields()
                    except ValidationError as e:
                        error_fields = list(dict(e).keys())
                        for field in error_fields:
                            setattr(company, field, None)

                    company.contacts_import_id = contacts_import_id
                    company.save()
                    _set_item_links(company, row, 'company')
            except Exception as e:
                transaction.rollback()
                company = None
                logger.warning('import_contacts: failed to create Company: {}'.format(smart_str(e)))
            else:
                if is_new:
                    companies_cnt += 1

                    if rows_cnt < 1000:
                        Activity.log_addition(company)
        else:
            company = None

        person_name = row.get('person_name')
        if person_name:
            try:
                with transaction.atomic():
                    is_new = True
                    if merge_contacts:
                        if 'extra_field' in person_merge_field:
                            merge_field_value = row.get(person_merge_field)
                            lookup = {
                                'field_id': person_merge_field[12:],
                                'value': merge_field_value,
                            }
                            if merge_field_value and ItemExtraFieldLink.objects.by_account(account).filter(item_type=ItemType.PERSON.value, **lookup).exists():
                                extra_field_value = ItemExtraFieldLink.objects.by_account(account).filter(item_type=ItemType.PERSON.value, **lookup).last()
                                person = extra_field_value.item
                                is_new = False
                        else:
                            merge_field_value = row.get('person_name' if person_merge_field == 'name' else person_merge_field)
                            lookup = {'{}__iexact'.format(person_merge_field): merge_field_value}
                            if merge_field_value and Person.objects.by_account(account).filter(**lookup).exists():
                                person = Person.objects.select_for_update().by_account(account).filter(**lookup).last()
                                is_new = False

                    if is_new:
                        person = Person(account=account, name=person_name, user=contacts_import.user)

                    _set_item_fields(person, row, COMMON_FIELDS + PERSON_FIELDS)

                    if company:
                        person.company = company

                    try:
                        person.clean_fields()
                    except ValidationError as e:
                        error_fields = list(dict(e).keys())
                        for field in error_fields:
                            setattr(person, field, None)

                    person.contacts_import_id = contacts_import_id
                    person.save()
                    _set_item_links(person, row, 'person')
            except Exception as e:
                transaction.rollback()
                person = None
                logger.warning('import_contacts: failed to create Person: {}'.format(smart_str(e)))
            else:
                if is_new:
                    persons_cnt += 1

                    if rows_cnt < 1000:
                        Activity.log_addition(person)
        else:
            person = None

        for codename, value in row.items():
            if not codename.startswith('extra_field_'):
                continue

            extra_field_id = codename[12:]
            try:
                extra_field = ExtraField.objects.by_account(account).get(id=extra_field_id)
            except ExtraField.DoesNotExist:
                logger.warning(
                    'import_contacts: failed to get ExtraField: id={}'.format(smart_str(extra_field_id))
                )
            else:
                if isinstance(value, float):
                    value = str(int(value))

                extra_fields = ExtraField.objects.by_account(account).filter(name__iexact=extra_field.name)
                for field in extra_fields:
                    if field.content_type.model == 'company' and company:
                        company.set_extra_field_value(field, value)
                        continue
                    if field.content_type.model == 'person' and person:
                        person.set_extra_field_value(field, value)
                        continue

    contacts_import.is_completed = True
    contacts_import.completed_at = tz.now()
    contacts_import.companies_cnt = companies_cnt
    contacts_import.persons_cnt = persons_cnt
    contacts_import.save(update_fields=('is_completed', 'completed_at', 'companies_cnt', 'persons_cnt'))


@app.task(name='crm.export_items')
def export_items(account_id, items_export_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        logger.warning('export_items failed: account does not exist (id={})'.format(account_id))
        return

    try:
        items_export = ItemsExport.objects.get(
            is_ready=False,
            id=items_export_id
        )
    except ItemsExport.DoesNotExist:
        return

    model = apps.get_model('crm', items_export.model_name)

    fields = [
        field for field in model._meta.fields if field.name not in (
            'id', 'user', 'created_at', 'is_archived', 'archived_at', 'updated_at', 'contacts_import', 'type', 'state',
            'completed_at', 'periodic_task',
        )
    ]
    extra_fields = ExtraField.objects.by_account(account).filter(content_type=ContentType.objects.get_for_model(model))

    f = BytesIO()

    if items_export.extension == ItemsExport.EXTENSION_CSV:
        writer = unicodecsv.writer(f, encoding='utf-8')
        writer.writerow(
            [field.verbose_name for field in fields] +
            [extra_field.name for extra_field in extra_fields] +
            [_('Assignees'), _('Tags')]
        )

        for ids_chunk in iter_chunks(items_export.item_ids, 100):
            qs = model.objects.by_account(account).select_related('user').filter(id__in=ids_chunk)
            if items_export.model_name == 'person':
                qs = qs.select_related('company')
            elif items_export.model_name == 'deal':
                qs = qs.select_related('company', 'person', 'currency', 'stage')
            elif items_export.model_name == 'task':
                qs = qs.select_related('company', 'person', 'deal')

            for item in qs:
                if items_export.model_name == 'deal':
                    if item.status != Deal.PENDING:
                        item.stage = None
                    item.status = item.get_status_display()
                elif items_export.model_name == 'task':
                    item.state = item.get_verbose_state()
                    if item.expire_date:
                        item.expire_date = formats.date_format(tz.localtime(item.expire_date), 'DATETIME_FORMAT')

                def _get_field_value(item_field):
                    item_field_value = getattr(item, item_field.name)
                    if not item_field_value:
                        return ''

                    if item_field.name in ('emails', 'phones'):
                        item_field_value = ', '.join(str(value) for value in item_field_value)

                    return str(item_field_value)

                responsible_links = item.get_responsible_links()
                responsibles = ', '.join(
                    get_user_account_name(link.account, link.user) for link in responsible_links
                )

                tag_links = item.get_tag_links()
                tags = ', '.join(link.tag.name for link in tag_links)

                row = (
                    list(map(_get_field_value, fields))
                    + [item.get_extra_field_value(extra_field) for extra_field in extra_fields]
                    + [responsibles, tags]
                )

                writer.writerow(row)
    elif items_export.extension == ItemsExport.EXTENSION_XLS:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = model._meta.verbose_name_plural[:31]

        column = 1
        for field in fields:
            ws.cell(row=1, column=column, value=smart_str(field.verbose_name))
            column += 1
        for extra_field in extra_fields:
            ws.cell(row=1, column=column, value=smart_str(extra_field.name))
            column += 1
        for field in [_('Assignees'), _('Tags')]:
            ws.cell(row=1, column=column, value=smart_str(field))
            column += 1

        row_num = 2
        for ids_chunk in iter_chunks(items_export.item_ids, 100):
            qs = model.objects.by_account(account).select_related('user').filter(id__in=ids_chunk)
            if items_export.model_name == 'person':
                qs = qs.select_related('company')
            elif items_export.model_name == 'deal':
                qs = qs.select_related('company', 'person', 'currency', 'stage')
            elif items_export.model_name == 'task':
                qs = qs.select_related('company', 'person', 'deal')

            for item in qs:
                if items_export.model_name == 'deal':
                    if item.status != Deal.PENDING:
                        item.stage = None
                    item.status = item.get_status_display()
                elif items_export.model_name == 'task':
                    item.state = item.get_verbose_state()
                    if item.expire_date:
                        item.expire_date = formats.date_format(tz.localtime(item.expire_date), 'DATETIME_FORMAT')

                column = 1
                for field in fields:
                    field_value = getattr(item, field.name)
                    if field.name in ('emails', 'phones') and field_value:
                        field_value = '\n'.join(str(value) for value in field_value)
                    elif field.name in ('company', 'person', 'deal', 'currency', 'stage'):
                        field_value = str(field_value) if field_value else ''

                    ws.cell(row=row_num, column=column, value=smart_str(field_value))
                    column += 1

                for extra_field in extra_fields:
                    extra_field_value = item.get_extra_field_value(extra_field)
                    if extra_field_value:
                        if extra_field.type == ExtraField.TYPE_DATETIME:
                            extra_field_value = formats.date_format(tz.localtime(extra_field_value), 'DATETIME_FORMAT')
                        elif extra_field.type == ExtraField.TYPE_DATE:
                            extra_field_value = formats.date_format(tz.localtime(extra_field_value), 'DATE_FORMAT')
                    ws.cell(row=row_num, column=column, value=smart_str(extra_field_value))
                    column += 1

                responsible_links = item.get_responsible_links()
                responsibles = ', '.join(
                    get_user_account_name(link.account, link.user) for link in responsible_links
                )
                ws.cell(row=row_num, column=column, value=smart_str(responsibles))
                column += 1

                tag_links = item.get_tag_links()
                tags = ', '.join(link.tag.name for link in tag_links)
                ws.cell(row=row_num, column=column, value=smart_str(tags))

                row_num += 1

        wb.save(f)

    items_export.result.save('{}.{}'.format(MODEL_PLURALS[items_export.model_name], items_export.extension), File(f))
    items_export.is_ready = True
    items_export.save(update_fields=('result', 'is_ready'))


@app.task(name='crm.archive_items')
def archive_items(account_id, model_name, item_ids):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        logger.warning('archive_items failed: account does not exist (id={})'.format(account_id))
        return

    model = apps.get_model('crm', model_name)
    scoped_ids = model.objects.by_account(account).filter(id__in=item_ids).values_list('id', flat=True)
    model.archive(list(scoped_ids))


@app.task(name='crm.update_tasks_state')
def update_tasks_state():
    for account in Account.objects.all():
        tasks = Task.objects.by_account(account).filter(state=Task.STATE_PENDING)
        for task in tasks:
            if task.expire_date and task.expire_date + dt.timedelta(hours=24) < tz.now():
                task.state = Task.STATE_OVERDUE
                task.save(update_fields=('state',))


@app.task(name='crm.create_periodic_tasks')
def create_periodic_tasks():
    now = tz.now()
    today = now.date()

    for account in Account.objects.all():
        periodic_tasks = PeriodicTask.objects.by_account(account)
        for periodic_task in periodic_tasks:
            if Task.objects.by_account(account).filter(
                periodic_task_id=periodic_task.id,
                expire_date__gte=now
            ).exists():
                continue

            if periodic_task.period == PeriodicTask.PERIOD_WEEK:
                for weekday in periodic_task.weekdays:
                    next_date = today + dt.timedelta(days=(weekday - today.isoweekday()))
                    if next_date < today:
                        continue

                    periodic_task.create_task(account, next_date)
            elif periodic_task.period == PeriodicTask.PERIOD_MONTH:
                for month in periodic_task.months:
                    if month < today.month:
                        continue

                    for monthday in periodic_task.monthdays:
                        next_date = today.replace(month=month, day=monthday)
                        periodic_task.create_task(account, next_date)


@app.task(name='crm.clean_archived_items')
def clean_archived_items(account_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        return

    now = tz.now()
    date = now - dt.timedelta(days=settings.CLEAN_ARCHIVED_ITEMS_DAYS)

    Activity.all_objects.by_account(account).filter(is_archived=True, archived_at__lte=date).delete()
    Upload.all_objects.by_account(account).filter(is_archived=True, archived_at__lte=date).delete()
    Note.all_objects.by_account(account).filter(is_archived=True, archived_at__lte=date).delete()

    task_ids = list(Task.all_objects.by_account(account).filter(is_archived=True, archived_at__lte=date).values_list('id', flat=True))
    ItemExtraFieldLink.objects.by_account(account).filter(
        item_type=Task.ITEM_TYPE,
        item_id__in=task_ids
    ).delete()
    ItemResponsibleLink.objects.by_account(account).filter(
        item_type=Task.ITEM_TYPE,
        item_id__in=task_ids
    ).delete()
    ItemTagLink.objects.by_account(account).filter(
        item_type=Task.ITEM_TYPE,
        item_id__in=task_ids
    ).delete()
    Task.all_objects.filter(id__in=task_ids).delete()

    deal_ids = list(Deal.all_objects.by_account(account).filter(is_archived=True, archived_at__lte=date).values_list('id', flat=True))
    ItemExtraFieldLink.objects.by_account(account).filter(
        item_type=Deal.ITEM_TYPE,
        item_id__in=deal_ids
    ).delete()
    ItemResponsibleLink.objects.by_account(account).filter(
        item_type=Deal.ITEM_TYPE,
        item_id__in=deal_ids
    ).delete()
    ItemTagLink.objects.by_account(account).filter(
        item_type=Deal.ITEM_TYPE,
        item_id__in=deal_ids
    ).delete()
    Deal.all_objects.filter(id__in=deal_ids).delete()

    person_ids = list(
        Person.all_objects.by_account(account).filter(is_archived=True, archived_at__lte=date).values_list('id', flat=True)
    )
    ItemExtraFieldLink.objects.by_account(account).filter(
        item_type=Person.ITEM_TYPE,
        item_id__in=person_ids
    ).delete()
    ItemResponsibleLink.objects.by_account(account).filter(
        item_type=Person.ITEM_TYPE,
        item_id__in=person_ids
    ).delete()
    ItemTagLink.objects.by_account(account).filter(
        item_type=Person.ITEM_TYPE,
        item_id__in=person_ids
    ).delete()
    Person.all_objects.filter(id__in=person_ids).delete()

    company_ids = list(
        Company.all_objects.by_account(account).filter(is_archived=True, archived_at__lte=date).values_list('id', flat=True)
    )
    ItemExtraFieldLink.objects.by_account(account).filter(
        item_type=Company.ITEM_TYPE,
        item_id__in=company_ids
    ).delete()
    ItemResponsibleLink.objects.by_account(account).filter(
        item_type=Company.ITEM_TYPE,
        item_id__in=company_ids
    ).delete()
    ItemTagLink.objects.by_account(account).filter(
        item_type=Company.ITEM_TYPE,
        item_id__in=company_ids
    ).delete()
    Company.all_objects.filter(id__in=company_ids).delete()
