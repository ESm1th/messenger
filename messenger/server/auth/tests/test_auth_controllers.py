import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import (
    User,
    Base
)
from auth.controllers import (
    register,
    login
)


engine = create_engine('sqlite:///:memory:')


def setup_function(function):
    Base.metadata.create_all(engine)


def teardown_function(function):
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='module')
def valid_request():
    return {
        'data': {
            'username': 'test_user',
            'password': 'qwerty'
        }
    }


@pytest.fixture(scope='module')
def make_session():
    session = sessionmaker(bind=engine)
    return session()


@pytest.fixture(scope='function')
def make_user_session(make_session):
    session = make_session
    user = User(username='test_user', password='qwerty')
    session.add(user)
    session.commit()
    return session


def test_register_no_user_exists(valid_request, make_session):
    response = register(valid_request, make_session)
    assert response.get('code') == 200


def test_register_user_exists(valid_request, make_user_session):
    response = register(valid_request, make_user_session)
    assert response.get('code') == 205


def test_login(valid_request, make_user_session):
    response = login(valid_request, make_user_session)
    assert response.get('code') == 200


def test_login_wrong_password(valid_request, make_user_session):
    request = valid_request
    request.update(
        {
            'data':
            {
                'username': 'test_user',
                'password': 'wrong_password'
            }
        }
    )
    response = login(request, make_user_session)

    assert response.get('code') == 205
    assert response.get('data') == 'Wrong password'


def test_login_username_not_exists(make_user_session):
    request = {'data': {'username': 'not_exists_user'}}
    response = login(request, make_user_session)

    assert response.get('code') == 205
    assert response.get('data') == 'Username does not exists'


def test_login_no_data(make_user_session):
    request = {}
    response = login(request, make_user_session)

    assert response.get('code') == 400
