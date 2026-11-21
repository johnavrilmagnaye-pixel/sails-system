from datetime import timedelta
import os

from celery.schedules import crontab


CELERY_TIMEZONE = os.environ.get('TIME_ZONE', 'UTC')
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_WORKER_DISABLE_RATE_LIMITS = True
CELERY_TASK_IGNORE_RESULT = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True



CELERY_TASK_ROUTES = {
    # emails
    'core.tasks.send_email': {'queue': 'emails'},

    # periodic_starters
    'crm.remind_tasks_starter': {'queue': 'periodic_starters'},
    'crm.clean_archived_items_starter': {'queue': 'periodic_starters'},

    # crm
    'crm.notify_responsibles': {'queue': 'crm'},
    'crm.set_remind_task_links': {'queue': 'crm'},
    'crm.remind_tasks': {'queue': 'crm'},
    'crm.update_tasks_state': {'queue': 'crm'},
    'crm.create_periodic_tasks': {'queue': 'crm'},
    'crm.import_contacts': {'queue': 'crm'},
    'crm.clean_archived_items': {'queue': 'crm'},
    'crm.send_tasks_digest_starter': {'queue': 'crm'},
    'crm.notifications_deal_added': {'queue': 'crm'},
    'crm.notifications_task_added': {'queue': 'crm'},
}




CELERY_BEAT_SCHEDULE = {
    # crm
    'crm.remind_tasks_starter': {
        'task': 'crm.remind_tasks_starter',
        'schedule': timedelta(minutes=1),
    },
    # 'crm.send_tasks_digest_starter': {
    #     'task': 'crm.send_tasks_digest_starter',
    #     'schedule': crontab(minute='*', day_of_week='mon-fri'),
    # },
    'crm.update_tasks_state': {
        'task': 'crm.update_tasks_state',
        'schedule': timedelta(minutes=1),
    },
    'crm.create_periodic_tasks': {
        'task': 'crm.create_periodic_tasks',
        'schedule': timedelta(hours=1),
    },
    'crm.clean_archived_items_starter': {
        'task': 'crm.clean_archived_items_starter',
        'schedule': crontab(hour=3, minute=33),
    },
}

try:
    from .local import *
except ImportError:
    pass
