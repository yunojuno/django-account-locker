from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from account_locker import lockout

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

        if lockout.is_account_locked(username):
            logger.info("Account is locked")
            messages.error(request, "Your account is locked.")
            return None
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
            logger.info("Invalid password for user %s", username)
            messages.error(request, "Invalid username / password combination.")
        except User.DoesNotExist:
            logger.info("Invalid username %s", username)
            messages.error(request, "Invalid username / password combination.")
        if lockout.handle_failed_login(username, request):
            messages.error(request, "Your account has been locked.")
        return None
