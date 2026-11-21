from enum import IntEnum, StrEnum

from django.utils.translation import gettext_noop


DEFAULT_DEAL_STAGES = (
    (gettext_noop('Negotiation'), 0),
    (gettext_noop('Proposal'), 1),
    (gettext_noop('Contract'), 2),
    (gettext_noop('Invoice'), 3),
    (gettext_noop('Payment'), 4),
    (gettext_noop('Closing documents'), 5),
)

DEAL_CURRENCIES = (
    (gettext_noop('US dollar'), 'USD', '${}'),
    (gettext_noop('Euro'), 'EUR', '{} €'),
    (gettext_noop('Pound sterling'), 'GBP', '£{}'),
    (gettext_noop('Swiss franc'), 'CHF', None),
    (gettext_noop('Yuan'), 'CNY', '¥{} CNY'),
    (gettext_noop('Hong Kong dollar'), 'HKD', 'HK$ {}'),
    (gettext_noop('Canadian dollar'), 'CAD', '${} CAD'),
    (gettext_noop('Hryvnia'), 'UAH', '{} UAH'),
    (gettext_noop('Russian ruble'), 'RUB', '{} RUB'),
    (gettext_noop('Belarusian ruble'), 'BYR', '{} BYR'),
    (gettext_noop('Tenge'), 'KZT', '{} KZT'),
    (gettext_noop('Yen'), 'JPY', '¥{} JPY'),
    (gettext_noop('Danish krone'), 'DKK', None),
    (gettext_noop('Norwegian krone'), 'NOK', None),
    (gettext_noop('Swedish krona'), 'SEK', None),
    (gettext_noop('Czech koruna'), 'CZK', None),
    (gettext_noop('Bulgarian lev'), 'BGN', None),
    (gettext_noop('Azerbaijani manat'), 'AZN', None),
    (gettext_noop('Armenian dram'), 'AMD', None),
    (gettext_noop('Estonian kroon'), 'EEK', None),
    (gettext_noop('Lari'), 'GEL', None),
    (gettext_noop('New Israeli shekel'), 'ILS', None),
    (gettext_noop('Som'), 'KGS', None),
    (gettext_noop('Won'), 'KRW', '₩{} KRW'),
    (gettext_noop('Lithuanian litas'), 'LTL', None),
    (gettext_noop('Latvian lats'), 'LVL', None),
    (gettext_noop('Moldovan leu'), 'MDL', None),
    (gettext_noop('Zloty'), 'PLN', None),
    (gettext_noop('Baht'), 'THB', None),
    (gettext_noop('Turkmenistan manat'), 'TMT', None),
    (gettext_noop('Uzbekistani sum'), 'UZS', None),
    (gettext_noop('Dong'), 'VND', None),
    (gettext_noop('Somoni'), 'TJS', None),
    (gettext_noop('Item count'), 'pcs', None),
)

DEFAULT_CURRENCY_CODES = ('USD', 'EUR')


class UserRole(IntEnum):
    OWNER = 1
    ADMIN = 2
    MANAGER = 3


class UserPermission(StrEnum):
    COMPANY_ADD = 'add_company'
    COMPANY_VIEW_ALL = 'view_all_company'
    COMPANY_CHANGE_OWN = 'change_own_company'
    COMPANY_CHANGE_ASSIGNED = 'change_assigned_company'
    COMPANY_CHANGE_ALL = 'change_all_company'
    COMPANY_DELETE_OWN = 'delete_own_company'

    PERSON_ADD = 'add_person'
    PERSON_VIEW_ALL = 'view_all_person'
    PERSON_CHANGE_OWN = 'change_own_person'
    PERSON_CHANGE_ASSIGNED = 'change_assigned_person'
    PERSON_CHANGE_ALL = 'change_all_person'
    PERSON_DELETE_OWN = 'delete_own_person'

    DEAL_ADD = 'add_deal'
    DEAL_VIEW_ALL = 'view_all_deal'
    DEAL_CHANGE_OWN = 'change_own_deal'
    DEAL_CHANGE_ASSIGNED = 'change_assigned_deal'
    DEAL_CHANGE_ALL = 'change_all_deal'
    DEAL_DELETE_OWN = 'delete_own_deal'

    TASK_ADD = 'add_task'
    TASK_VIEW_ALL = 'view_all_task'
    TASK_CHANGE_OWN = 'change_own_task'
    TASK_CHANGE_ASSIGNED = 'change_assigned_task'
    TASK_DELETE_OWN = 'delete_own_task'

    NOTE_ADD = 'add_note'
    NOTE_VIEW_ALL = 'view_all_note'
    NOTE_DELETE_OWN = 'delete_own_note'

    UPLOAD_ADD = 'add_upload'
    UPLOAD_VIEW_ALL = 'view_all_upload'
    UPLOAD_DELETE_OWN = 'delete_own_upload'
