from __future__ import annotations


class AccountLocked(Exception):
    # deliberately vague.
    default_message = "This account is locked, please try again in a few minutes."

    def __init__(self, message: str = default_message):
        super().__init__(message)
