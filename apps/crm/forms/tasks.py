from django import forms
from django.conf import settings

from crm.models import Task, ItemExtraFieldLink, ItemType

from .base import BaseItemForm


__all__ = (
    'TaskForm',
)


class TaskForm(BaseItemForm):
    model_name = 'task'

    class Meta:
        model = Task
        fields = ('name', 'company', 'person', 'deal', 'expire_date', 'tags', 'responsibles', 'details',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['expire_date'].input_formats = settings.DATETIME_INPUT_FORMATS
        self.fields['expire_date'].widget = forms.DateTimeInput(format=settings.DATETIME_INPUT_FORMATS[0])

        if self.account.is_gta:
            self.fields['expire_date'].required = True

    def get_extra_field_initial(self, extra_field):
        if not self.instance.id:
            return None

        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.TASK.value,
                item_id=self.instance.id,
                field_id=extra_field.id
            )
        except ItemExtraFieldLink.DoesNotExist:
            return None

        return link.get_value()


class TaskChangeDateForm(forms.Form):
    expire_date = forms.DateTimeField(required=True, input_formats=settings.DATETIME_INPUT_FORMATS)
