from django.core.mail import get_connection, EmailMultiAlternatives
from django.core.mail.backends.base import BaseEmailBackend

from core.tasks import send_email


class CeleryEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently)
        self.init_kwargs = kwargs

    def send_messages(self, email_messages, **kwargs):
        results = []
        kwargs['_backend_init_kwargs'] = self.init_kwargs
        for msg in email_messages:
            results.append(send_email.delay(msg, **kwargs))
        return results


def send_html_mail(subject, text_message, html_message, from_email, recipient_list, headers):
    connection = get_connection(username=None, password=None, fail_silently=False)

    message = EmailMultiAlternatives(
        subject, text_message, from_email, recipient_list, connection=connection, headers=headers
    )
    message.attach_alternative(html_message, 'text/html')

    return message.send()
