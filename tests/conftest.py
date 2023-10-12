import pytest
from django.http import HttpRequest
from django.test import RequestFactory


@pytest.fixture
def login_request(rf: RequestFactory) -> HttpRequest:
    return rf.post("/sign-in", HTTP_USER_AGENT="test")
