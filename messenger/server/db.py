from sqlalchemy.ext.declarative import declarative_base
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
def session_scope():
    """Provide a transactional scope around a series of operations."""

    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class DefaultFieldsMixin():
    """
    Mixin adds following default fields for classes:
    id, created (timestamp), updated (timestamp)
    """

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    updated = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now()
    )


class User(DefaultFieldsMixin, Base):
    """Represents 'users' table in database"""

    __tablename__ = 'users'

    first_name = Column(String)
    second_name = Column(String)
    username = Column(String, unique=True, nullable=False)
    phone = Column(String)
    email = Column(String)
    avatar_id = Column(Integer, ForeignKey('media.id'))
    bio = Column(Text)
    password = Column(String, nullable=False)

    # relationships
    messages = relationship(
        'Message',
        order_by='Message.id',
        back_populates='user'
    )
    chats = relationship('Chat', back_populates='creator')
    avatar = relationship('Media', back_populates='user')

    def __repr__(self):
        return '<User, first_name={0}, second_name={1}, username={2}>'.format(
            self.first_name,
            self.second_name,
            self.username
        )


class Chat(DefaultFieldsMixin, Base):
    """Represents 'chats' table in database"""

    __tablename__ = 'chats'

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
        return '<Chat, id={0}, type={1}, creator={2}>'.format(
            self.id,
            self.type,
            self.creator
        )


class Message(DefaultFieldsMixin, Base):
    """Represents 'messages' table in database"""

    __tablename__ = 'messages'

    text = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    chat_id = Column(Integer, ForeignKey('chats.id'))
    media_id = Column(Integer, ForeignKey('media.id'))
    
    # relationships
    user = relationship('User', back_populates='messages')
    chat = relationship('Chat', back_populates='messages')
    media = relationship('Media', back_populates='message')

    def __repr__(self):
        return '<Message, id={0}, user={1}, chat={2}>'.format(
            self.id,
            self.user,
            self.chat
        )


class Media(DefaultFieldsMixin, Base):
    """Represents 'media' table in database"""

    __tablename__ = 'media'

    path = Column(String)

    # relationships
    message = relationship('Message', uselist=False, back_populates='media')
    user = relationship('User', uselist=False, back_populates='avatar')
    chat = relationship('Chat', uselist=False, back_populates='picture')

    def __repr__(self):
        return '<Media, id={0}, path={1}, message={2}>'.format(
            self.id,
            self.path,
            self.message
        )


Base.metadata.create_all(engine)