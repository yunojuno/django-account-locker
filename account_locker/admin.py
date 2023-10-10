from __future__ import annotations

from django.contrib import admin

from .models import FailedLogin


@admin.register(FailedLogin)
class FailedLoginAdmin(admin.ModelAdmin):
    list_display = ("username", "ip_address", "timestamp")
    search_fields = ("username", "ip_address", "user_agent")
    list_filter = ("timestamp",)
    readonly_fields = ("username", "ip_address", "user_agent", "timestamp")
