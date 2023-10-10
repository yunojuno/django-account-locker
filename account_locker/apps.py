from django.apps import AppConfig


class AccountLockerConfig(AppConfig):
    name = "account_locker"
    verbose_name = "Account login attempt limiter"
    default_auto_field = "django.db.models.BigAutoField"
