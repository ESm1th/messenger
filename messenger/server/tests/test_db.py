import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import (
    Base,
    SessionScope,
    Client,
    ClientHistory,
    Contact
)


engine = create_engine('sqlite:///:memory:')


def setup_function(function):
    Base.metadata.create_all(engine)


def teardown_function(function):
    Base.metadata.drop_all(engine)


@pytest.fixture
def make_session(scope='function'):
    session = sessionmaker(bind=engine)
    return session


@pytest.fixture(scope='function')
def creat_user(make_session):
    Client.create(make_session, username='test_user', password='qwerty')


def test_create_user(make_session, creat_user):
    user = Client.get_client(make_session, 'test_user')

    assert user is not None
    assert user.password == 'qwerty'


def test_client_history(make_session, creat_user):
    user = Client.get_client(make_session, 'test_user')
    history = ClientHistory.create(
        make_session, address='10.0.16.100', client_id=user.id
    )

    with SessionScope(make_session) as session:
        user = session.query(Client).filter(
            Client.username == user.username).one_or_none()
        history = session.query(ClientHistory).filter(
            ClientHistory.client_id == user.id).one_or_none()

        assert user.history[0] == history
        assert user.history[0].address == history.address
        assert user.history[0].client_id == history.client_id


def test_contact(make_session, creat_user):
    contacts_owner = Client.get_client(make_session, 'test_user')
    users = ('test_1', 'test_2', 'test_3')

    for user in users:
        contact = Client.create(make_session, username=user, password=user)

    with SessionScope(make_session) as session:

        for user in users:
            contact = session.query(Client).filter(
                Client.username == user).one_or_none()
            session.add(
                Contact(owner_id=contacts_owner.id, contact_id=contact.id)
            )

        session.commit()

    contacts = Contact.all(make_session)

    for contact in contacts:
        assert contact.owner_id is contacts_owner.id
