import os

from celery import Celery
from celery.signals import task_failure

from django.conf import settings
from django.core.mail import mail_admins


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')


app = Celery('project')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@task_failure.connect()
def celery_task_failure_email(**kwargs):
    task_id = kwargs.get('task_id')
    exception = kwargs.get('exception')
    sender = kwargs.get('sender')
    task = sender.name if sender else 'unknown'
    host = 'local' if settings.DEBUG else 'prod'

    subject = f"[celery@{host}] Error: Task {task} ({task_id}): {exception}"
    message = f"""
    Task {task} with id {task_id} raised exception: {exception}
    Task was called with args: {kwargs.get('args')} kwargs: {kwargs.get('kwargs')}.

    {kwargs.get('einfo')}
    """

    mail_admins(subject, message)
