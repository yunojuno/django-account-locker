import datetime

import pytest
from django.test import RequestFactory
from django.utils import timezone

from account_locker.models import FailedLogin, _parse_ip_address
from account_locker.settings import FAILED_LOGIN_INTERVAL_SECS


@pytest.mark.django_db
def test_gte_cutoff() -> None:
    username = "username"
    now = timezone.now()
    qs = FailedLogin.objects.filter(username=username)
    fl1 = FailedLogin.objects.create("username", None)
    assert str(fl1) == "Failed login for 'username'"
    assert qs.count() == 1
    # create a FailedLogin outside the cutoff window
    timestamp = now - datetime.timedelta(seconds=FAILED_LOGIN_INTERVAL_SECS)
    _ = FailedLogin.objects.create("username", None, timestamp=timestamp)
    assert qs.count() == 2
    assert qs.gte_cutoff().count() == 1
    assert qs.gte_cutoff().get() == fl1


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
