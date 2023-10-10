from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.messages import add_message
from django.http import HttpRequest

from account_locker.lockout import account_is_locked, lock_account
from account_locker.models import FailedLogin

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomAuthBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> settings.AUTH_USER_MODEL | None:
        if not username:
            return None

        if account_is_locked(username):
            logger.info("Account is locked")
            add_message(request, 40, "Your account is locked.")
            return None
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
            logger.info("Invalid password for user %s", username)
        except User.DoesNotExist:
            logger.info("Invalid username %s", username)
        FailedLogin.objects.create(
            username=username,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )
        if FailedLogin.objects.gte_max_limit(username):
            logger.info("Locking account %s", username)
            lock_account(username)
            add_message(request, 40, "Your account has been locked.")
        return None
