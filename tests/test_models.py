import datetime

import pytest
from django.test import RequestFactory
from django.utils import timezone

from account_locker.models import FailedLogin, _parse_ip_address


@pytest.mark.django_db
@pytest.mark.parametrize(
    "count,interval,result",
    [
        (1, 1, False),
        # 3 logins at 1s intervals = 0, 1, 2 - total interval = 2s
        (3, 1, True),
        # 3 logins at 14s intervals = 0, 14, 28 - trips lockout
        (3, 14, True),
        # 3 logins at 15s intervals = 0, 15, 30 + few ms - no lockout
        (3, 15, False),
    ],
)
def test_gte_max_limit(count: int, interval: int, result: bool) -> None:
    username = "username"
    max_limit = 3
    max_interval = 30
    now = timezone.now()
    # create a series of FailedLogins starting now and going
    # back in time, with `interval` between each.
    for i in range(count):
        timestamp = now - datetime.timedelta(seconds=i * interval)
        FailedLogin.objects.create("username", None, timestamp=timestamp)
    assert FailedLogin.objects.count() == count
    assert (
        FailedLogin.objects.gte_max_limit(
            username, limit=max_limit, interval=max_interval
        )
        == result
    )


@pytest.mark.parametrize(
    "forward_for,remote_addr,ip_address",
    [
        ("", "", ""),
        ("", "127.0.0.1", "127.0.0.1"),
        ("8.8.8.8", "127.0.0.1", "8.8.8.8"),
        ("8.8.8.8,9.9.9.9", "127.0.0.1", "8.8.8.8"),
    ],
)
def test__parse_ip_address(
    rf: RequestFactory, forward_for: str, remote_addr: str, ip_address: str
) -> None:
    request = rf.post("/", HTTP_X_FORWARDED_FOR=forward_for, REMOTE_ADDR=remote_addr)
    assert _parse_ip_address(request) == ip_address
