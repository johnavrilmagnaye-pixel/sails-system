import json

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe


register = template.Library()


@register.tag
def setting(parser, token):
    """
    Usage:
        {% load get_settings %}
        {% setting DEBUG %}
        {% setting DEBUG as debugging %}
    """

    split = token.split_contents()
    context_var = None
    option = None
    as_index = split.index('as') if 'as' in split else None

    if as_index is not None:
        try:
            context_var = split[as_index + 1]
        except IndexError:
            raise template.TemplateSyntaxError(
                f'Context variable assignment must take the form of {{%% {split[0]} DEBUG as debugging %%}}'
            )
        del split[as_index:as_index + 2]
    if len(split) == 2:
        option = split[1]
    else:
        raise template.TemplateSyntaxError(
            f'{split[0]} tag takes one required argument with optional context_var'
        )

    return SettingNode(option=option, context_var=context_var)


@register.tag
def json_setting(parser, token):
    split = token.split_contents()

    if len(split) != 2:
        raise template.TemplateSyntaxError(f'{split[0]} tag takes one required argument')

    option = split[1]

    return SettingNode(option=option, to_json=True)


class SettingNode(template.Node):
    def __init__(self, option, context_var=None, to_json=False):
        self.option = option
        self.context_var = context_var
        self.to_json = to_json

    def render(self, context):
        # if FAILURE then FAIL silently
        try:
            value = getattr(settings, self.option)
            if self.context_var:
                context[self.context_var] = value
                return ''
            else:
                if self.to_json:
                    return mark_safe(json.dumps(value))
                return str(value)
        except:
            return ''
