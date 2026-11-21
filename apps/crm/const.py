from enum import Enum


__all__ = (
    'ItemType',
    'ITEM_TYPE_CHOICES',
)


class ItemType(Enum):
    COMPANY = 'company'
    PERSON = 'person'
    DEAL = 'deal'
    TASK = 'task'
    PERIODIC_TASK = 'periodic_task'


ITEM_TYPE_CHOICES = (
    (ItemType.COMPANY.value, ItemType.COMPANY.value),
    (ItemType.PERSON.value, ItemType.PERSON.value),
    (ItemType.DEAL.value, ItemType.DEAL.value),
    (ItemType.TASK.value, ItemType.TASK.value),
    (ItemType.PERIODIC_TASK.value, ItemType.PERIODIC_TASK.value),
)
