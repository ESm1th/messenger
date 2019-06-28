import enum
import os
from contextlib import AbstractContextManager
from typing import List, Union

from sqlalchemy.ext.declarative import (
    declarative_base,
    declared_attr
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    sessionmaker,
    relationship,
    subqueryload,
    Session as SqlAlchemyOrmSession
)
from sqlalchemy import (
    Column,
    Table,
    Integer,
    Enum,
    Boolean,
    String,
    DateTime,
    Text,
    ForeignKey,
    create_engine,
    func
)

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
            session.add(self)

            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

            session.add(self)
            session.commit()
            session.refresh(self)

    def delete(self, seance) -> None:
        with SessionScope(seance) as session:
            session.delete(self)
            session.commit()


chat_association_table = Table(
    'chat_association',
    Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id')),
    Column('chat_id', Integer, ForeignKey('chats.id'))
)


class Client(CoreMixin, Base):  # type: ignore
    """Represents 'clients' table in database"""

    username = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    second_name = Column(String)
    bio = Column(Text)
    password = Column(String, nullable=False)
    _is_authenticate = Column(Integer, default=0)

    # relationships
    pictures = relationship('Media', back_populates='uploader')
    history = relationship('ClientHistory', back_populates='client')
    chats = relationship(
        'Chat',
        secondary=chat_association_table,
        back_populates='participants'
    )

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
            client = session.query(cls).options(
                subqueryload(cls.contacts).subqueryload('user')
            ).filter(cls.username == username).one_or_none()
            return client

    @hybrid_property
    def is_authenticate(self):
        return self._is_authenticate

    @is_authenticate.setter
    def is_authenticate(self, boolean: Boolean):

        if boolean:
            self._is_authenticate = 1
        else:
            self._is_authenticate = 0

    def set_auth_state(self, session, state):
        self.is_authenticate = state

        with SessionScope(session) as session:
            session.add(self)
            session.commit()
            session.refresh(self)

    def add_address(self, session, address):

        with SessionScope(session) as session:
            session.add(self)

            self.history.append(
                ClientHistory(address=address, client_id=self.id)
            )

            session.add(self)
            session.commit()
            session.refresh(self)

    def get_avatar(self, session):

        with SessionScope(session) as session:
            session.add(self)

            return next(
                (
                    picture for picture in self.pictures if picture.kind
                    == MediaTypes.AVATAR
                ),
                None
            )

    def set_avatar(self, session):

        with SessionScope(session) as session:
            session.add(self)

            self.pictures.append(
                Media(
                    uploader_id=self.id,
                    kind=MediaTypes.AVATAR,
                    path=f'{self.username}_avatar.png'
                )
            )

            session.add(self)
            session.commit()
            session.refresh(self)

    def delete_avatar(self, session):
        avatar = self.get_avatar(session)

        with SessionScope(session) as session:
            session.add(self)
            session.add(avatar)
            session.delete(avatar)
            session.commit()


class ClientHistory(CoreMixin, Base):  # type: ignore
    """Represents 'client history' table in database"""

    # time of entry is default field 'created' from CoreMixin
    address = Column(String)
    client_id = Column(Integer, ForeignKey('clients.id'))

    # relationships
    client = relationship('Client', back_populates='history')

    def __repr__(self) -> str:
        return '<{0}(address={1}, client_id={2})>'.format(
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
    user = relationship(
        'Client',
        foreign_keys=contact_id,
        backref='contact',
        lazy='subquery'
    )


class Chat(CoreMixin, Base):
    """Represents 'chats' table in database"""

    messages = relationship('Message', back_populates='chat')
    participants = relationship(
        'Client',
        secondary=chat_association_table,
        back_populates='chats',
    )


class Message(CoreMixin, Base):
    """Represents 'messages' table in database"""

    sender_id = Column(Integer, ForeignKey('clients.id'))
    receiver_id = Column(Integer, ForeignKey('clients.id'))
    chat_id = Column(Integer, ForeignKey('chats.id'))
    text = Column(String)

    chat = relationship('Chat', back_populates='messages')


class MediaTypes(enum.Enum):
    """Pictures types"""

    AVATAR = enum.auto()
    PICTURE = enum.auto()


class Media(CoreMixin, Base):
    """Represents 'media' table in database"""

    __tablename__ = 'media'

    kind = Column(Enum(MediaTypes))
    uploader_id = Column(Integer, ForeignKey('clients.id'))
    path = Column(String)

    uploader = relationship('Client', back_populates='pictures')

    def __repr__(self) -> str:
        return '<{0}(uploader={1}, path={2})>'.format(
            self.__class__.__name__,
            self.uploader_id,
            self.path
        )


Base.metadata.create_all(engine)
