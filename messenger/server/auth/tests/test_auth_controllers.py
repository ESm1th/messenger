import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import (
    User,
    Base
)
from auth.controllers import (
    Register,
    Login
)
from core import Request


engine = create_engine('sqlite:///:memory:')


def setup_function(function):
    Base.metadata.create_all(engine)


def teardown_function(function):
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='function')
def valid_request():
    return Request(data={
        'username': 'test_user',
        'password': 'qwerty',
        'repeat_password': 'qwerty'
        }
    )


@pytest.fixture(scope='module')
def make_session():
    session = sessionmaker(bind=engine)
    return session


@pytest.fixture(scope='function')
def make_user_session(make_session):
    session = make_session()
    user = User(username='test_user', password='qwerty')
    session.add(user)
    session.commit()
    return session


def test_register_no_user_exists(valid_request, make_session):
    response = Register(valid_request, make_session).process()
    assert response.data.get('code') == 200


def test_register_user_exists(
    valid_request,
    make_user_session,
    make_session
):  
    print(valid_request.data)
    response = Register(valid_request, make_session).process()
    assert response.data.get('code') == 205


def test_login(
    valid_request,
    make_user_session,
    make_session
):
    response = Login(valid_request, make_session).process()
    assert response.data.get('code') == 200


def test_login_wrong_password(
    valid_request,
    make_user_session,
    make_session
):
    request = valid_request
    request.data.update(
        {
            'username': 'test_user', 
            'password': 'wrong_password'
        }
    )
    response = Login(request, make_session).process()

    assert response.data.get('code') == 205
    assert response.data.get('info') == 'Wrong password'


def test_login_username_not_exists(make_user_session, make_session):
    request = Request(data={'username': 'not_exists_user', 'password': 'qwerty'})
    response = Login(request, make_session).process()

    assert response.data.get('code') == 205
    assert response.data.get('info') == 'Username does not exists'


def test_login_no_data(make_user_session, make_session):
    request = Request(data={})
    response = Login(request, make_session).process()

    assert response.data.get('code') == 400
