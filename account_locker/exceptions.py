from __future__ import annotations

from django.utils.translation import gettext_lazy as _lazy

from .settings import ACCOUNT_LOCKED_TIMEOUT_SECS


class AccountLocked(Exception):
    default_message = _lazy(
        "Account locked for {seconds} seconds. Please try again later.".format(
            seconds=ACCOUNT_LOCKED_TIMEOUT_SECS
        )
    )

    def __init__(self, message: str = default_message):
        super().__init__(message)
