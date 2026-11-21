from itertools import chain

from django import forms
from django.utils.encoding import force_str
from django.utils.html import format_html

from crm.models import Tag


class TagWidget(forms.SelectMultiple):
    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_str(v) for v in selected_choices)
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(format_html('<optgroup label="{0}">', force_str(option_value)))
                for option in option_label:
                    output.append(self.render_option(selected_choices, *option))
                output.append('</optgroup>')
            else:
                output.append(self.render_option(selected_choices, option_label, option_label))
        return '\n'.join(output)

    def render(self, name, value, attrs=None, choices=()):
        if value:
            value = [v for v in value if isinstance(v, int)]
            value = Tag.objects.filter(id__in=value).values_list('name', flat=True)

        return super().render(name, value, attrs, choices)
