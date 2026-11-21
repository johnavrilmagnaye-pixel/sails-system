import math
import re
from decimal import Decimal as D

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone as tz
from django.utils.encoding import force_str
from django.utils.log import AdminEmailHandler


def pluralize(number, form_one, form_two, form_five):
    """
    :param number:
    :param form_one: singular form
    :param form_two: paucal form
    :param form_five: plural form
    :return:
    """

    number = abs(int(number))
    a = number % 10
    b = number % 100

    if (a == 1) and (b != 11):
        return form_one
    elif 2 <= a <= 4 and (b < 10 or b >= 20):
        return form_two

    return form_five


def decimal_money(value, decimal_places=2):
    if not value:
        return 0

    value = D(str(value)[:26]).quantize(D(1) / pow(10, abs(decimal_places)))

    if value == 0:  # special case for '-0.00'
        return 0

    def intcomma(val):
        orig = force_str(val)
        new = re.sub(r"^(-?\d+)(\d{3})", r'\g<1> \g<2>', orig)

        if orig == new:
            return new

        return intcomma(new)

    value = intcomma(value)

    return value.rstrip('0').rstrip('.') if '.' in value else value


def email_admins(subject, message):
    text_context = {
        'content': message
    }
    html_context = {
        'content': message.replace('\n', '<br>')
    }

    from core.tasks import send_mail
    for _, to_email in settings.ADMINS:
        send_mail.delay(
            subject,
            render_to_string('notifications/custom/email.txt', text_context),
            render_to_string('notifications/custom/email.html', html_context),
            to_email,
            settings.SERVER_EMAIL,
        )


def is_holidays():
    now = tz.now()

    month = now.month
    day = now.day

    if (
        (month == 12 and day == 31) or
        (month == 1 and day in range(1, 7)) or
        (month == 5 and day in range(1, 3)) or
        (month == 5 and day in range(7, 10))
    ):
        return True

    return False


def iter_chunks(items, chunk_size):
    for i in range(int(math.ceil(len(items) / chunk_size))):
        chunk = items[i * chunk_size:(i + 1) * chunk_size]
        yield chunk


def as_int(value, default=None, min=None, max=None, allow_none=False):
    """
    Convert value to an int and limit it to the given range, or return default
    if conversion fails.
    """

    if allow_none and value is None:
        return None

    try:
        res = int(value)
    except (TypeError, ValueError):
        return default

    if min is not None and res < min:
        res = min
    elif max is not None and res > max:
        res = max

    return res


class InternalErrorHandler(AdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        context = {
            'content': message.replace('\n', '<br>'),
        }

        from core.tasks import send_mail
        html_message = render_to_string('notifications/custom/email.html', context)
        from_email = settings.SERVER_EMAIL

        for _, to_email in settings.ADMINS:
            send_mail.delay(subject, message, html_message, to_email, from_email)
