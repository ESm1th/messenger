from sqlalchemy.ext.declarative import (
    declarative_base,
    declared_attr
)
from sqlalchemy.orm import (
    sessionmaker,
    relationship,
    subqueryload,
    Session as SqlAlchemyOrmSession
)
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    create_engine,
    func
)
from contextlib import AbstractContextManager
from typing import List, Union

from settings import BASE_DIR

engine = create_engine('sqlite:///{0}/db.sqlite'.format(BASE_DIR), echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class SessionScope(AbstractContextManager):
    """SQLAlchemy orm session context manager"""

    def __init__(self, session) -> None:
        self.session = session()

    def __enter__(self) -> SqlAlchemyOrmSession:
        return self.session

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type:
            self.session.rollback()
        self.session.close()


class CoreMixin:
    """Provide default functionality for ancestors"""

    @declared_attr
    def __tablename__(cls) -> str:
        return '{0}s'.format(cls.__name__.lower())

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())

    @classmethod
    def all(cls, seance) -> List:
        with SessionScope(seance) as session:
            return session.query(cls).all()

    @classmethod
    def create(cls, seance, *args, **kwargs) -> None:
        with SessionScope(seance) as session:
            obj = cls(**kwargs)
            session.add(obj)
            session.commit()

    def update(self, seance, *args, **kwargs) -> None:
        with SessionScope(seance) as session:
            for key, value in kwargs.items():
                setattr(self, key, value)
            session.add(self)
            session.commit()

    def delete(self, seance) -> None:
        with SessionScope(seance) as session:
            session.delete(self)
            session.commit()


class Client(CoreMixin, Base):  # type: ignore
    """Represents 'clients' table in database"""

    username = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    second_name = Column(String)
    bio = Column(Text)
    password = Column(String, nullable=False)

    # relationships
    history = relationship('ClientHistory', back_populates='client')

    def __repr__(self) -> str:
        return '<{0}(first_name={1}, second_name={2}, username={3})>'.format(
            self.__class__.__name__,
            self.first_name,
            self.second_name,
            self.username
        )

    @classmethod
    def get_client(cls, session, username) -> Union['Client', None]:
        with SessionScope(session) as session:
            return session.query(cls).options(
                subqueryload(cls.contacts).subqueryload('user')
            ).filter(cls.username == username).one_or_none()


class ClientHistory(CoreMixin, Base):  # type: ignore
    """Represents 'client history' table in database"""

    # time of entry is default field 'created' from CoreMixin
    address = Column(String)
    client_id = Column(Integer, ForeignKey('clients.id'))

    # relationships
    client = relationship('Client', back_populates='history')

    def __repr__(self) -> str:
        return '<{0}(address={1}, client_is={2})>'.format(
            self.__class__.__name__,
            self.address,
            self.client_id
        )


class Contact(CoreMixin, Base):  # type: ignore
    """Represents 'contacts' table in database"""

    owner_id = Column(Integer, ForeignKey('clients.id'))
    contact_id = Column(Integer, ForeignKey('clients.id'))

    # relationships
    owner = relationship(
        'Client',
        foreign_keys=owner_id,
        backref='contacts',
        lazy='subquery'
    )
    user = relationship('Client', foreign_keys=contact_id)


class Chat(CoreMixin, Base):
    """Represents 'chats' table in database"""

    participant_id = Column(Integer, ForeignKey('clients.id'))

    # participant = relationship('Client')
    messages = relationship('Message', back_populates='chat')
    participant = relationship(
        'Client',
        backref='chats',
        primaryjoin='Chat.participant_id==Client.id'
    )


class Message(CoreMixin, Base):
    """Represents 'messages' table in database"""

    sender_id = Column(Integer, ForeignKey('clients.id'))
    receiver_id = Column(Integer, ForeignKey('clients.id'))
    chat_id = Column(Integer, ForeignKey('chats.id'))
    text = Column(String)

    chat = relationship('Chat', back_populates='messages')


Base.metadata.create_all(engine)
