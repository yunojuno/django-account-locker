from datetime import timedelta

from django.conf import settings

# the time interval in which failed login attempts are counted (60s)
FAILED_LOGIN_INTERVAL_SECS = int(getattr(settings, "FAILED_LOGIN_INTERVAL_SECS", 60))
# the same value as a timedeleta
FAILED_LOGIN_INTERVAL = timedelta(seconds=FAILED_LOGIN_INTERVAL_SECS)

# the maximum number of failed login attempts before an account is locked (4)
MAX_FAILED_LOGIN_ATTEMPTS = int(getattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 4))

# the time an account is locked (60s) - used to set cache timeout
ACCOUNT_LOCKED_TIMEOUT_SECS = int(getattr(settings, "ACCOUNT_LOCKED_TIMEOUT_SECS", 60))
# the time an account is locked (60s) as a timedelta
ACCOUNT_LOCKED_TIMEOUT = timedelta(seconds=ACCOUNT_LOCKED_TIMEOUT_SECS)
