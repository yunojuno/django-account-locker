# django-account-locker

Django app for managing failed logins and account lockout.

## Compatibility

This package supports:
- Python 3.12+ and Django 5.2-6.0

## Background

Email / password logins (without MFA) are vulnerable to Brute Force attacks
where a malicious party can attempt to crack the password by cycling through
a list of password for a given username (email).

One mitigation for this is "Account lockout", whereby an account is locked
when a certain threshold of X failures in Y time period is exceeded. This
is what this package implements, in its simplest possible form.

**Note on Account Lockouts**

OWASP itself is equivocal on the subject of account lockouts, as they can
be used in extremis to DOS a service by locking out all of their users, and
overwhelming their support team with requests to unlock.

https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks

Use with caution, and if in doubt use something additional measures like MFA,
or remove passwords altogether and use SSO, Passkeys etc.

## Implementation

This packages satisfies two requirements:

1. Log all failures for future reference / investigation
2. Apply temporary lock to prevent further logins for a period of time.

### Failure logging

This package includes a model called `FailedLogin` which records the
username and request info (IP address, user agent).

NB This locking mechanism operates at the username level, and **not**
a the `User` account level. This is to prevent another attack, Account
Enumeration, whereby an attacker can determine which accounts are real.

This package locks the string used as the username - it makes no difference
whether that relates to a real account or not. It is essentially saying "You
cannot continue to try this username for a period".

### Account lockout

The lockout process is very simple and backed by the Django cache. When
a failed login tips the account over the threshold a cache entry is set
for the period configured as the lockout, and if that cache entry exists
all further login attempts can be ignored.

## Configuration

There are three settings that manage the threshold. The default
threshold is "4 failed logins in 60 seconds locks the account for 60
seconds". The individual settings are below.

#### `MAX_FAILED_LOGIN_ATTEMPTS`

The number of failed logins within the `FAILED_LOGIN_INTERVAL_SECS`
required to trip a lockout. Defaults to 4.

#### `FAILED_LOGIN_INTERVAL_SECS`

The interval over which failed logins should be considered - e.g. if the
threshold is "3 attempts in 30s", this value is `30`. Defaults to 60.

#### `ACCOUNT_LOCKED_TIMEOUT_SECS`

The duration (in seconds) of the lockout period, in the event that the
number of failed logins within the `FAILED_LOGIN_INTERVAL_SECS` exceeds
the limit set by `MAX_FAILED_LOGIN_ATTEMPTS`. Defaults to 60.

## Demo app

The actual login class is left out of the core package, and is up to you
to implement. The `demo` app provided in the source distribution does
include an authentication backend called `CustomAuthBackend` which
demonstrates a very simple implementation.

```python
class CustomAuthBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> settings.AUTH_USER_MODEL | None:

        # if the username is already locked - ignore authentication
        if lockout.is_account_locked(username):
            logger.info("Account is locked")
            messages.error(request, "Your account is locked.")
            return None

        # attempt to authenticate normally
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
            # password supplied was invalid - log and continue
            logger.info("Invalid password for user %s", username)
            messages.error(request, "Invalid username / password combination.")
        except User.DoesNotExist:
            # username supplied was invalid - log and continue
            logger.info("Invalid username %s", username)
            messages.error(request, "Invalid username / password combination.")

        # either username or login failed - record the login
        # this will return True if the account has been locked
        lockout.handle_failed_login(username, request)
        if lockout.is_account_locked(username):
            messages.error(request, "Your account has been locked.")
        return None
```

If you manage your login failure using exceptions, you can use the `raise_if_locked`
method:

```python
class CustomAuthBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> settings.AUTH_USER_MODEL | None:

        # if the username is already locked raise AccountLocked
        lockout.raise_if_locked(username)

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            lockout.handle_failed_login(username, request):

        # have we now tripped the AccountLocked exception?
        lockout.raise_if_locked(username)

```

All of this is wrapped up in a decorator called `apply_account_lock`,
which wraps the `ModelBackend.authenticate` method. The simplest
possible implementation is therefore:

```python
class CustomModelBackend(ModelBackend):
    @apply_account_lock
    def authenticate(self, request, **credentials) -> User | None:
        super().authenticate(self, **credentials):
```
