from django import forms
from django.core.exceptions import ValidationError

from crm.models import Tag
from crm.widgets import TagWidget


class AccountFieldMixin:
    """Limit a model choice field to objects owned by one account."""

    def __init__(self, *args, account=None, **kwargs):
        self.account = account
        super().__init__(*args, **kwargs)
        self.set_account(account)

    def set_account(self, account):
        self.account = account
        self.queryset = self.queryset.by_account(account)


class AccountModelChoiceField(AccountFieldMixin, forms.ModelChoiceField):
    pass


class AccountModelMultipleChoiceField(AccountFieldMixin, forms.ModelMultipleChoiceField):
    pass


class TagField(forms.ModelMultipleChoiceField):
    widget = TagWidget
    account = None

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_account(account)

    def set_account(self, account):
        self.account = account
        self.queryset = Tag.objects.none() if account is None else Tag.objects.by_account(account)

    def clean(self, value):
        if not value:
            return Tag.objects.none()

        for tag in value:
            Tag.objects.get_or_create(account=self.account, name=tag)

        return Tag.objects.by_account(self.account).filter(name__in=value)
