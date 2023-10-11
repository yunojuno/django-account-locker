from __future__ import annotations

import pytest
from django.core.cache import cache
from django.test import RequestFactory

from account_locker import lockout
from account_locker.exceptions import AccountLocked
from account_locker.models import FailedLogin
from account_locker.settings import MAX_FAILED_LOGIN_ATTEMPTS


def test_account_locking_cache() -> None:
    # default state - nothing in the cache, account is not locked
    assert not cache.get("users:account_lockout:username")
    assert not lockout.is_account_locked("username")
    # lock the account and check the cache
    lockout.lock_account("username")
    assert cache.get("users:account_lockout:username")
    assert lockout.is_account_locked("username")
    # unlock the account and check the cache is empty
    lockout.unlock_account("username")
    assert not cache.get("users:account_lockout:username")
    assert not lockout.is_account_locked("username")


@pytest.mark.django_db
def test_handle_failed_login(rf: RequestFactory) -> None:
    request = rf.post("/sign-in", HTTP_USER_AGENT="foo")
    qs = FailedLogin.objects.filter(username="username")
    assert qs.count() == 0
    assert not lockout.is_account_locked("username")
    # add failed logins up to the limit
    for i in range(MAX_FAILED_LOGIN_ATTEMPTS):
        assert not lockout.is_account_locked("username")
        lockout.handle_failed_login("username", request)
        assert qs.count() == i + 1
    # check the account is now locked
    assert lockout.is_account_locked("username")
    cache.clear()
    assert not lockout.is_account_locked("username")


def test_raise_if_locked() -> None:
    # account is not locked
    lockout.raise_if_locked("username")
    # lock account and try again
    lockout.lock_account("username")
    with pytest.raises(AccountLocked):
        lockout.raise_if_locked("username")


def test_raise_if_locked__custom_error() -> None:
    class CustomError(Exception):
        def __init__(self, message: str) -> None:
            self.message = message

    with pytest.raises(CustomError) as excinfo:
        lockout.raise_if_locked("username", exception_type=CustomError, message="foo")
    assert str(excinfo.value.message) == "foo"
