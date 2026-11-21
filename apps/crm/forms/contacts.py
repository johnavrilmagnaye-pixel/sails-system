from django.core import validators

from crm.models import Company, Person, ItemExtraFieldLink, ItemType

from .base import BaseItemForm


__all__ = (
    'CompanyForm',
    'PersonForm',
)


class CompanyForm(BaseItemForm):
    model_name = 'company'

    class Meta:
        model = Company
        fields = ('name', 'address', 'website', 'phones', 'emails', 'tags', 'responsibles', 'details')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['website'].widget.input_type = 'text'

    def get_extra_field_initial(self, extra_field):
        if not self.instance.id:
            return None

        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.COMPANY.value,
                item_id=self.instance.id,
                field_id=extra_field.id
            )
        except ItemExtraFieldLink.DoesNotExist:
            return None

        return link.get_value()

    def clean_phones(self):
        phones = self.cleaned_data.get('phones') or []
        return [phone for phone in phones if phone]

    def clean_emails(self):
        emails = self.cleaned_data.get('emails') or []
        return [email for email in emails if email]


class PersonForm(BaseItemForm):
    model_name = 'person'

    class Meta:
        model = Person
        fields = ('name', 'company', 'post', 'phones', 'emails', 'tags', 'responsibles', 'details')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_extra_field_initial(self, extra_field):
        if not self.instance.id:
            return None

        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.PERSON.value,
                item_id=self.instance.id,
                field_id=extra_field.id
            )
        except ItemExtraFieldLink.DoesNotExist:
            return None

        return link.get_value()

    def clean_phones(self):
        phones = self.cleaned_data.get('phones') or []
        return [phone for phone in phones if phone]

    def clean_emails(self):
        emails = self.cleaned_data.get('emails') or []
        return [email for email in emails if email]
