from django import forms
from django.utils.translation import gettext_lazy as _

from crm.models import ExtraField


__all__ = (
    'ExportForm',
    'ExtraFieldForm',
)


EXTENSION_CHOICES = (
    ('csv', 'CSV'),
    ('xls', 'XLS (Excel)')
)


class ExportForm(forms.Form):
    extension = forms.ChoiceField(widget=forms.RadioSelect, choices=EXTENSION_CHOICES, label=_("File format"), initial='csv')
    
    
class ExtraFieldForm(forms.ModelForm):
    class Meta:
        model = ExtraField
        fields = ('name',)

    def __init__(self, content_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if content_type:
            self.instance.content_type = content_type

    def clean_name(self):
        extra_field_qs = ExtraField.objects.filter(name__iexact=self.cleaned_data['name'], content_type=self.instance.content_type)
        if self.instance.id:
            extra_field_qs = extra_field_qs.exclude(id=self.instance.id)

        if extra_field_qs.exists():
            raise forms.ValidationError(_('An extra field with this name already exists.'))

        base_fields = [field.verbose_name.lower() for field in self.instance.content_type.model_class()._meta.fields]
        if self.cleaned_data['name'].lower() in base_fields:
            raise forms.ValidationError(_('A field with this name already exists.'))

        return self.cleaned_data['name']
