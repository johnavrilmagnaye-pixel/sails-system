from django import template

from core import utils


register = template.Library()


@register.filter()
def decimal_money(value, decimal_places=2):
    return utils.decimal_money(value, decimal_places)
