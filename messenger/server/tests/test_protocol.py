import pytest
from datetime import datetime

from core import (
    Request,
    Router
)


@pytest.fixture
def valid_request(scope='module'):
    return Request(
        action='register',
        time=datetime.now().timestamp(),
        data='Test string'
    )


@pytest.fixture
def invalid_request(scope='module'):
    return Request()


def test_validate_valid_request(valid_request):
    assert valid_request.is_valid() is True


def test_validate_invalid_request(invalid_request):
    assert invalid_request.is_valid() is False


def test_request_with_valid_action(valid_request):
    assert Router().validate_action(valid_request.action) is True


def test_validate_invalid_action(invalid_request):
    assert Router().validate_action(invalid_request.action) is None
