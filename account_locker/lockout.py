from __future__ import annotations

from django.core.cache import cache

from .settings import ACCOUNT_LOCKED_TIMEOUT_SECS


def _cache_key(username: str) -> str:
    return f"users:account_lockout:{username}"


def lock_account(username: str) -> None:
    cache.set(_cache_key(username), True, ACCOUNT_LOCKED_TIMEOUT_SECS)


def unlock_account(username: str) -> None:
    cache.delete(_cache_key(username))


def account_is_locked(username: str) -> bool:
    return bool(cache.get(_cache_key(username), False))
