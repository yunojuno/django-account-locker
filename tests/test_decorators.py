from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import User
from django.http.request import HttpRequest

from account_locker import lockout
from account_locker.decorators import apply_account_lockout
from account_locker.models import FailedLogin
from account_locker.settings import MAX_FAILED_LOGIN_ATTEMPTS


class CustomModelBackend(ModelBackend):
    @apply_account_lockout
    def authenticate(
        self,
        request: HttpRequest,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> AbstractBaseUser | None:
        return super().authenticate(request, username, password, **kwargs)


@pytest.mark.django_db
class TestApplyAccountLockDecorator:
    @pytest.fixture
    def backend(self) -> CustomModelBackend:
        return CustomModelBackend()

    def test_authenticate_missing_username(self, backend: CustomModelBackend) -> None:
        assert backend.authenticate(None, None, None) is None

    def test_allows_valid_login(self, backend: CustomModelBackend) -> None:
        user = User.objects.create_user(username="username", password="xxx")
        assert backend.authenticate(None, "username", "xxx") == user
        assert FailedLogin.objects.count() == 0

    def test_adds_failed_login(
        self,
        backend: CustomModelBackend,
        login_request: HttpRequest,
    ) -> None:
        lockout.unlock_account("username")
        qs = FailedLogin.objects.filter(username="username")
        for i in range(MAX_FAILED_LOGIN_ATTEMPTS - 1):
            backend.authenticate(login_request, username="username", password="xxx")
            assert qs.count() == i + 1

    def test_raises_account_locked(
        self,
        backend: CustomModelBackend,
        login_request: HttpRequest,
    ) -> None:
        lockout.lock_account("username")
        with pytest.raises(lockout.AccountLocked):
            backend.authenticate(login_request, username="username", password="xxx")
