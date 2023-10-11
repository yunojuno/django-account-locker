from __future__ import annotations

import datetime
from typing import Any

from django.db import models
from django.http import HttpRequest
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


class FailedLoginManager(models.Manager):
    def create(self, username: str, request: HttpRequest, **kwargs: Any) -> Any:
        """Create a FailedLogin object."""
        kwargs["user_agent"] = request.META.get("HTTP_USER_AGENT")[:255]
        # X-Forwarded-For is used by convention when passing through
        # load balancers etc., as the REMOTE_ADDR is rewritten in transit
        kwargs["ip_address"] = (
            request.META.get("HTTP_X_FORWARDED_FOR")
            if "HTTP_X_FORWARDED_FOR" in request.META
            else request.META.get("REMOTE_ADDR", "")
        )[:39]
        return super().create(username=username, **kwargs)


class FailedLogin(models.Model):
    """Store failed login attempts."""

    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=tz_now)

    objects = FailedLoginManager.from_queryset(FailedLoginQuerySet)()

    def __str__(self) -> str:
        return f"FailedLogin for {self.username}"


def raise_if_exceeds_limit(username: str) -> None:
    """Raise an exception if the account is locked."""
    if FailedLogin.objects.gte_max_limit(username):
        raise AccountLocked
