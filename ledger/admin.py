from django.contrib import admin
from .models import (
    Account,
    LedgerEntry
)

admin.site.register(Account)
admin.site.register(LedgerEntry)