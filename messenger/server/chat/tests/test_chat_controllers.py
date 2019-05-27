import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from db import (
    Client,
    Contact,
    Base,
    SessionScope
)
from chat.controllers import Contacts
from core import Request


engine = create_engine('sqlite:///:memory:')


def setup_function(function):
    Base.metadata.create_all(engine)


def teardown_function(function):
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='function')
def valid_request():
    return Request(data={
        'action': 'get_contacts',
        'time': datetime.now().timestamp(),
        'username': 'test_1',
        }
    )


@pytest.fixture(scope='module')
def make_session():
    session = sessionmaker(bind=engine)
    return session


@pytest.fixture(scope='function')
def test_user(make_session):
    Client.create(make_session, username='test_user', password='test_password')
    return Client.get_client(make_session, username='test_user')


@pytest.fixture(scope='function')
def fill_db(make_session):
    clients = {
        'test_1': 1,
        'test_2': 2,
        'test_3': 3,
        'test_4': 4,
        'test_5': 5
    }

    for client, password in clients.items():
        Client.create(make_session, username=client, password=password)

    user = Client.get_client(make_session, 'test_1')
    clients.pop('test_1')

    for client in clients:
        contact = Client.get_client(make_session, client)
        Contact.create(make_session, owner_id=user.id, contact_id=contact.id)


def test_get_contacts_if_contacts_exists(
    valid_request,
    make_session,
    fill_db,
    test_user
):
    response = Contacts(valid_request, make_session).process()

    assert response.data.get('code') == 202
    assert test_user not in response.data.get('info')


def test_get_contacts_if_contacts_not_exists(
    valid_request,
    make_session,
    test_user
):
    valid_request.data.update({'username': 'test_user'})
    response = Contacts(valid_request, make_session).process()

    assert response.data.get('code') == 202
    assert response.data.get('info') == 'Your contacts list is empty' 
