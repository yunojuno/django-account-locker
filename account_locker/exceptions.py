from __future__ import annotations


class AccountLocked(Exception):
    default_message = "Account is locked"

    def __init__(self, message: str = default_message):
        super().__init__(message)
