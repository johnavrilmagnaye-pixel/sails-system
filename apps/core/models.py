from django.db import models


class ByAccountQuerySet(models.QuerySet):
    def by_account(self, account):
        return self.filter(account=account)


class ByAccountManager(models.Manager.from_queryset(ByAccountQuerySet)):
    pass


class UnarchivedManager(ByAccountManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    objects = UnarchivedManager()
    all_objects = ByAccountManager()

    class Meta:
        abstract = True
