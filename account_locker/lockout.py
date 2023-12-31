from __future__ import annotations

import logging

from django.core.cache import cache
from django.http import HttpRequest
from django.utils.timezone import now as tz_now

from .exceptions import AccountLocked
from .models import FailedLogin
from .settings import ACCOUNT_LOCKED_TIMEOUT_SECS, MAX_FAILED_LOGIN_ATTEMPTS

logger = logging.getLogger(__name__)


def _cache_key(username: str) -> str:
    return f"users:account_lockout:{username}"


def lock_account(username: str, seconds: int = ACCOUNT_LOCKED_TIMEOUT_SECS) -> None:
    """Mark an account as locked for a short period."""
    logger.debug("Locking account '%s' for %s seconds", username, seconds)
    cache.set(_cache_key(username), tz_now(), seconds)


def unlock_account(username: str) -> None:
    """Unlock an account by removing cache entry."""
    logger.debug("Unlocking account '%s'", username)
    cache.delete(_cache_key(username))


def is_account_locked(username: str) -> bool:
    """Return True if the account is within its lockout period."""
    if timestamp := cache.get(_cache_key(username), None):
        logger.debug(
            "Account '%s' locked at %s, for %s seconds",
            username,
            timestamp,
            ACCOUNT_LOCKED_TIMEOUT_SECS,
        )
        return True
    return False


def raise_if_locked(username: str) -> None:
    """
    Raise error if account is locked.

    By default this will raise AccountLocked, but you can override this
    by passing in a new exception class and its kwargs.

    """
    if is_account_locked(username):
        raise AccountLocked


def handle_failed_login(username: str, request: HttpRequest) -> bool:
    """
    Add a failed login and lock account if necessary.

    Returns True if account is now locked.

    """
    logger.debug("Adding failed login for '%s'", username)
    FailedLogin.objects.create(username=username, request=request)
    if (
        FailedLogin.objects.filter(username=username).gte_cutoff().count()
        >= MAX_FAILED_LOGIN_ATTEMPTS
    ):
        lock_account(username)
        return True
    return False
