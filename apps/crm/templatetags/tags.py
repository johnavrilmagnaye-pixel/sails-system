from django import template


register = template.Library()


@register.simple_tag
def get_extra_field_value(item, extra_field):
    return item.get_extra_field_value(extra_field)
