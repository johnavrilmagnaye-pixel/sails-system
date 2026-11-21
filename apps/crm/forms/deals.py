from crm.models import Deal, DealCurrency, ItemExtraFieldLink, ItemType

from .base import BaseItemForm


__all__ = (
    'DealForm',
)


class DealForm(BaseItemForm):
    model_name = 'deal'

    class Meta:
        model = Deal
        fields = (
            'name', 'company', 'person', 'budget', 'currency', 'status', 'stage', 'tags', 'responsibles', 'details',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['budget'].widget.input_type = 'text'
        self.fields['currency'].queryset = DealCurrency.objects.by_account(self.account).filter(is_enabled=True)

    def get_extra_field_initial(self, extra_field):
        if not self.instance.id:
            return None

        try:
            link = ItemExtraFieldLink.objects.by_account(self.account).get(
                item_type=ItemType.DEAL.value,
                item_id=self.instance.id,
                field_id=extra_field.id
            )
        except ItemExtraFieldLink.DoesNotExist:
            return None

        return link.get_value()
