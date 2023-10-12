from __future__ import annotations

from typing import Any, Callable, TypeAlias

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from .lockout import handle_failed_login, raise_if_locked

AuthenticateMethodSignature: TypeAlias = Callable[
    [ModelBackend, HttpRequest, str | None, str | None, Any],
    settings.AUTH_USER_MODEL | None,
]


def apply_account_lockout() -> Callable:
    """
    Decorate ModelBackend.authenticate() to throttle login attempts.

    This decorator wraps the authenticate() method of the ModelBackend
    class to log failed login attempts and lock accounts after a certain
    number of failed attempts.

    A failed login is defined as a call to authenticate() that returns
    None - this could mean that the username does not exist or the
    password is invalid - both are treated the same. If you attempt to
    login and you get nothing back that is a failure.

    If the number of failed login attempts for a given username exceeds
    the number of attempts allowed within the interval specified, the
    account is locked for the duration specified, and the decorator
    raises the AccountLocked exception.

    """

    def decorator(func: AuthenticateMethodSignature) -> AuthenticateMethodSignature:
        def wrapper(
            instance: ModelBackend,
            request: HttpRequest,
            username: str | None = None,
            password: str | None = None,
            **kwargs: Any,
        ) -> settings.AUTH_USER_MODEL | None:
            if not username or not password:
                return None
            raise_if_locked(username)
            result = func(instance, request, username, password, **kwargs)  # type: ignore
            if result is None:
                handle_failed_login(username, request)
                raise_if_locked(username)
            return result

        return wrapper  # type: ignore

    return decorator
