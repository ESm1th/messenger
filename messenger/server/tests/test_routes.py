import pytest
from core import Router
from echo.controllers import get_echo


@pytest.fixture(scope='module')
def get_router():
    return Router()


@pytest.fixture(scope='module')
def get_controller():
    return lambda arg: print(arg)


def test_resolve_valid_action(get_router):
    router = get_router
    resolved = router.resolve('echo')
    assert resolved == get_echo


def test_resolve_invalid_action(get_router, get_controller):
    router = get_router
    resolved = router.resolve('echo')
    assert resolved != get_controller
