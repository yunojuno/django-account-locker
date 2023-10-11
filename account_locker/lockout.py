from __future__ import annotations

from django.core.cache import cache
from django.http import HttpRequest

from .exceptions import AccountLocked
from .models import FailedLogin
from .settings import ACCOUNT_LOCKED_TIMEOUT_SECS


def _cache_key(username: str) -> str:
    return f"users:account_lockout:{username}"


def lock_account(username: str) -> None:
    """Mark an account as locked for a short period."""
    cache.set(_cache_key(username), True, ACCOUNT_LOCKED_TIMEOUT_SECS)


def unlock_account(username: str) -> None:
    """Unlock an account by removing cache entry."""
    cache.delete(_cache_key(username))


def account_is_locked(username: str) -> bool:
    """Return True if the account is within its lockout period."""
    return bool(cache.get(_cache_key(username), False))


def raise_if_locked(
    username: str,
    message: str = AccountLocked.default_message,
    raise_exception: type[Exception] = AccountLocked,
) -> None:
    """
    Raise AccountLocked error if account is locked.

    The default message is deliberately vague, but you can overwite it
    with the message kwarg if you want to be more specific.

    The default exception raised is AccountLocked, but you can override
    this by passing in a new exception class with the raise_exception
    kwarg.

    """
    if account_is_locked(username):
        raise raise_exception(message)


def handle_failed_login(username: str, request: HttpRequest) -> bool:
    """
    Add a failed login and lock account if necessary.

    Returns True if account is now locked.

    """
    FailedLogin.objects.create(username=username, request=request)
    if FailedLogin.objects.gte_max_limit(username):
        lock_account(username)
        return True
    return False
