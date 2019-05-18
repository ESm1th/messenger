from sqlalchemy.ext.declarative import (
    declarative_base,
    declared_attr
)
from sqlalchemy.orm import (
    sessionmaker,
    relationship
)
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Enum,
    Boolean,
    ForeignKey,
    create_engine,
    func
)
from contextlib import contextmanager


engine = create_engine('sqlite:///db.sqlite', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# session_scope function realisation from SQLAlchemy origin
# https://docs.sqlalchemy.org/en/13/orm/session_basics.html

@contextmanager
def session_scope(session):
    """Provide a transactional scope around a series of operations."""
    session = session()
    try:
        yield session
    except Exception as error:
        session.rollback()
        raise error
    finally:
        session.close()


class CoreMixin:
    """Provide default functionality for ancestors"""

    @declared_attr
    def __tablename__(cls):
        return '{0}s'.format(cls.__name__.lower())

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    updated = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def all(cls, session):
        with session_scope(session) as session:
            return session.query(cls).all()

    @classmethod
    def create(cls, session, *args, **kwargs):
        with session_scope(session) as session:
            obj = cls(*args, **kwargs)
            session.add(obj)
            session.commit()

    def update(self, session, *args, **kwargs):
        with session_scope(session) as session:
            for key, value in kwargs.items():
                setattr(self, key, value)
            session.add(self)
            session.commit()

    def delete(self, session):
        with session_scope(session) as session:
            session.delete(self)
            session.commit()


class User(CoreMixin, Base):
    """Represents 'users' table in database"""

    first_name = Column(String)
    second_name = Column(String)
    username = Column(String, unique=True, nullable=False)
    phone = Column(String)
    email = Column(String)
    avatar_id = Column(Integer, ForeignKey('media.id'))
    bio = Column(Text)
    password = Column(String, nullable=False)
    logged = Column(Boolean, default=False)

    # relationships
    messages = relationship(
        'Message',
        order_by='Message.id',
        back_populates='user'
    )
    chats = relationship('Chat', back_populates='creator')
    avatar = relationship('Media', back_populates='user')

    def __repr__(self):
        return '<User(first_name={0}, second_name={1}, username={2})>'.format(
            self.first_name,
            self.second_name,
            self.username
        )

    @classmethod
    def get_user(cls, session, username):
        with session_scope(session) as session:
            return session.query(cls).filter(
                cls.username == username).one_or_none()


class Chat(CoreMixin, Base):
    """Represents 'chats' table in database"""

    title = Column(String)
    type = Column(Enum('single', 'group', name='type_of_chat'))
    creator_id = Column(Integer, ForeignKey('users.id'))
    picture_id = Column(Integer, ForeignKey('media.id'))

    # relationships
    creator = relationship('User', back_populates='chats')
    messages = relationship(
        'Message',
        order_by='Message.id',
        back_populates='chat'
    )
    picture = relationship('Media', back_populates='chat')

    def __repr__(self):
        return '<Chat(id={0}, type={1}, creator={2})>'.format(
            self.id,
            self.type,
            self.creator
        )


class Message(CoreMixin, Base):
    """Represents 'messages' table in database"""

    text = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    chat_id = Column(Integer, ForeignKey('chats.id'))
    media_id = Column(Integer, ForeignKey('media.id'))

    # relationships
    user = relationship('User', back_populates='messages')
    chat = relationship('Chat', back_populates='messages')
    media = relationship('Media', back_populates='message')

    def __repr__(self):
        return '<Message(id={0}, user={1}, chat={2})>'.format(
            self.id,
            self.user,
            self.chat
        )


class Media(CoreMixin, Base):
    """Represents 'media' table in database"""

    __tablename__ = 'media'

    path = Column(String)

    # relationships
    message = relationship('Message', uselist=False, back_populates='media')
    user = relationship('User', uselist=False, back_populates='avatar')
    chat = relationship('Chat', uselist=False, back_populates='picture')

    def __repr__(self):
        return '<Media(id={0}, path={1}, message={2})>'.format(
            self.id,
            self.path,
            self.message
        )


Base.metadata.create_all(engine)
