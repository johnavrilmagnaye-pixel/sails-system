from django.contrib import admin

from accounts.models import Account


class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('name',)


admin.site.register(Account, AccountAdmin)
