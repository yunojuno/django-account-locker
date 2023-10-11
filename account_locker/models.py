from __future__ import annotations

import datetime
from typing import Any

from django.db import models
from django.http import HttpRequest
from django.utils.timezone import now as tz_now

from .settings import (
    FAILED_LOGIN_INTERVAL_SECS,
)


def _parse_ip_address(request: HttpRequest) -> str:
    """Return source ip address from a request."""
    if not request:
        return ""
    if forwarded_for := request.META.get("HTTP_X_FORWARDED_FOR"):
        # split for multiple ips, and take the first
        return forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR", "")


def _parse_user_agent(request: HttpRequest) -> str:
    """Return the user agent string."""
    if not request:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


class FailedLoginQuerySet(models.QuerySet):
    def gte_cutoff(
        self,
        seconds: int = FAILED_LOGIN_INTERVAL_SECS,
    ) -> bool:
        """Filter queryset to the cutoff window."""
        cutoff = tz_now() - datetime.timedelta(seconds=seconds)
        return self.order_by("-timestamp").filter(timestamp__gte=cutoff)


class FailedLoginManager(models.Manager):
    def create(self, username: str, request: HttpRequest, **kwargs: Any) -> Any:
        """Create a FailedLogin object."""
        kwargs["user_agent"] = _parse_user_agent(request)[:39]
        kwargs["ip_address"] = _parse_ip_address(request)[:255]
        return super().create(username=username, **kwargs)


class FailedLogin(models.Model):
    """Store failed login attempts."""

    username = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=tz_now)

    objects = FailedLoginManager.from_queryset(FailedLoginQuerySet)()

    def __str__(self) -> str:
        return f"FailedLogin for '{self.username}'"
