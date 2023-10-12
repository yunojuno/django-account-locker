from __future__ import annotations

from datetime import datetime

import pytest
from django.core.cache import cache
from django.http import HttpRequest

from account_locker import lockout
from account_locker.exceptions import AccountLocked
from account_locker.models import FailedLogin
from account_locker.settings import MAX_FAILED_LOGIN_ATTEMPTS


class TestAccountLocking:
    def test_unlock_account(self) -> None:
        # default state - nothing in the cache, account is not locked
        lockout.unlock_account("username")
        assert not cache.get("users:account_lockout:username")
        assert not lockout.is_account_locked("username")

    def test_lock_account(self) -> None:
        # lock the account and check the cache
        lockout.lock_account("username")
        assert isinstance(cache.get("users:account_lockout:username"), datetime)
        assert lockout.is_account_locked("username")


@pytest.mark.django_db
def test_handle_failed_login(login_request: HttpRequest) -> None:
    qs = FailedLogin.objects.filter(username="username")
    lockout.unlock_account("username")
    # add failed logins up to the limit
    for i in range(MAX_FAILED_LOGIN_ATTEMPTS):
        assert not lockout.is_account_locked("username")
        lockout.handle_failed_login("username", login_request)
        assert qs.count() == i + 1
    # check the account is now locked
    assert lockout.is_account_locked("username")


def test_raise_if_locked() -> None:
    # account is not locked
    lockout.unlock_account("username")
    lockout.raise_if_locked("username")
    # lock account and try again
    lockout.lock_account("username")
    with pytest.raises(AccountLocked):
        lockout.raise_if_locked("username")
