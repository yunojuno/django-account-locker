from __future__ import annotations

import datetime

from django.db import models
from django.utils.timezone import now as tz_now

from .exceptions import AccountLocked
from .settings import (
    FAILED_LOGIN_INTERVAL_SECS,
    MAX_FAILED_LOGIN_ATTEMPTS,
)


class FailedLoginQuerySet(models.QuerySet):
    def gte_max_limit(
        self,
        username: str,
        limit: int = MAX_FAILED_LOGIN_ATTEMPTS,
        interval: int = FAILED_LOGIN_INTERVAL_SECS,
    ) -> bool:
        """Return True if the number of failed logins exceeds stated limits."""
        window = tz_now() - datetime.timedelta(seconds=interval)
        return (
            self.order_by("-timestamp")
            .filter(username=username, timestamp__gte=window)
            .count()
            >= limit
        )


class FailedLogin(models.Model):
    """Store failed login attempts."""

    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=tz_now)

    objects = FailedLoginQuerySet.as_manager()

    def __str__(self) -> str:
        return f"FailedLogin for {self.username}"


def raise_if_exceeds_limit(username: str) -> None:
    """Raise an exception if the account is locked."""
    if FailedLogin.objects.gte_max_limit(username):
        raise AccountLocked
