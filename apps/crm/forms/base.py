from django import forms
from django.contrib.auth.models import User

from crm.formfields import TagField
from crm.models import ExtraField, Tag


class BaseItemForm(forms.ModelForm):
    model_name = None

    account = None
    user = None

    tags = TagField(queryset=Tag.objects.all(), required=False)
    responsibles = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        if self.account:
            self.fields['tags'].set_account(self.account)
            self.fields['responsibles'].queryset = User.objects.filter(
                useraccountlink__account=self.account,
                useraccountlink__is_active=True,
                is_active=True,
            ).distinct()
            for field_name in ('company', 'person', 'deal', 'stage', 'currency'):
                field = self.fields.get(field_name)
                if field is not None and hasattr(field, 'queryset'):
                    field.queryset = field.queryset.by_account(self.account)

        self.init_extra_fields()

    def get_extra_field_initial(self, extra_field):
        raise NotImplementedError

    def init_extra_fields(self):
        self.Meta.fields = [field for field in self.Meta.fields if 'extra_field' not in field]
        for extra_field in ExtraField.objects.by_account(self.account).filter(content_type__model=self.model_name):
            initial = self.get_extra_field_initial(extra_field)

            form_extra_field_name = 'extra_field_{}'.format(extra_field.id)
            if extra_field.type == ExtraField.TYPE_DATE:
                self.fields[form_extra_field_name] = forms.DateField(required=False, initial=initial)
            elif extra_field.type == ExtraField.TYPE_DATETIME:
                self.fields[form_extra_field_name] = forms.DateTimeField(required=False, initial=initial)
            elif extra_field.is_number:
                self.fields[form_extra_field_name] = forms.DecimalField(required=False, initial=initial)
            elif extra_field.is_json:
                self.fields[form_extra_field_name] = forms.JSONField(required=False, initial=initial)
                self.fields[form_extra_field_name].empty_values.append([''])
            else:
                self.fields[form_extra_field_name] = forms.CharField(required=False, max_length=1000, initial=initial)

            if extra_field.is_required:
                self.fields[form_extra_field_name].required = True

    def save(self, commit=True):
        item = super().save(commit=False)

        if not self.instance.id:
            item.user = self.user
            item.account = self.account

        if commit:
            item.save()

            for extra_field in ExtraField.objects.by_account(self.account).filter(content_type__model=self.model_name):
                form_extra_field_name = 'extra_field_{}'.format(extra_field.id)
                if form_extra_field_name in self.changed_data:
                    item.set_extra_field_value(extra_field, self.cleaned_data[form_extra_field_name])

        return item
