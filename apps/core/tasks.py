from celery.utils.log import get_task_logger

from django.core.mail import EmailMultiAlternatives, get_connection

from project.celery import app


logger = get_task_logger(__name__)


@app.task(default_retry_delay=15*60)
def send_email(message, **kwargs):
    conn = get_connection(**kwargs.pop('_backend_init_kwargs', {}))

    try:
        result = conn.send_messages([message])
        logger.info("Successfully sent email message to %r.", message.to)
        return result
    except Exception as e:
        logger.warning("Failed to send email message to %r, retrying.", message.to)
        send_email.retry(exc=e)


@app.task(default_retry_delay=15*60)
def send_mail(subject, text_message, html_message, to_email, from_email, headers=None):
    recipients = [to_email] if isinstance(to_email, str) else list(to_email)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=from_email,
        to=recipients,
        headers=headers,
    )
    message.attach_alternative(html_message, 'text/html')

    try:
        message.send()
        logger.info("Successfully sent mail to {}.".format(to_email))
    except Exception as e:
        logger.warning('send_mail failed: {}, retrying.'.format(to_email))
        send_mail.retry(exc=e)
