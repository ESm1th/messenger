import re
from abc import ABC
from hashlib import pbkdf2_hmac
from pymongo import MongoClient
from bson.objectid import ObjectId

from settings import MONGO_CREDENTIALS, SALT


client = MongoClient(**MONGO_CREDENTIALS)
db = client.messenger


class Core(ABC):
    """Provide default functionality for ancestors"""

    collection = None
    fields = ()

    def __init__(self, *args, **kwargs):
        """
        Create attributes from passed kwargs.
        If '_id' not in kwargs also creates new database document.
        """
        properties = self.adapt_kwargs_to_class(kwargs)
        self.set_features(**properties)

        if '_id' not in kwargs:
            result = self.collection.insert_one(properties)
            self._id = result.inserted_id

    def set_features(self, **kwargs):
        """
        Sets attributes to object from passed kwargs.
        For every key from passed kwargs if object has this key in self.fields
        attribute then sets key's value to object attribute with name like key.
        """
        [
            setattr(self, feature, value)
            for feature, value in kwargs.items()
        ]

    def adapt_kwargs_to_class(self, kwargs):
        """
        Returns new dict with key, value pairs from passed dict
        if class has attribute with name like key name in these pairs.
        """
        return {
            feature: value
            for feature, value in kwargs.items() if feature in self.fields
        }

    @property
    def id(self):
        return self._id.binary.hex()

    @classmethod
    def get_by_id(cls, id):
        user_doc = cls.collection.find_one({'_id': ObjectId(id)})
        if user_doc:
            return cls(**user_doc)

    @classmethod
    def all(cls):
        """Returns all documents of collection"""
        return [
            document for document in cls.collection.find()
        ]

    def update(self, *args, **kwargs):
        """
        Updates document in mongo database and then updates own attributes
        """
        properties = self.adapt_kwargs_to_class(kwargs)
        result = self.collection.update_one(
            {'_id': self._id}, {'$set': properties}
        )
        if result:
            self.set_features(**properties)

    def delete(self):
        """Deletes document from mongo database"""
        self.collection.delete_one({'_id': self._id})  # check links to object


class User(Core):

    collection = db.users

    fields = (
        '_id',
        'username',
        'first_name',
        'second_name',
        'bio',
        'password',
        'avatar',
        'chats',
        'contacts',
        'is_authenticate'
    )

    def __init__(self, **kwargs):
        """
        Hashes password if object's document not in mongo database and then
        creates record in database and class instance attribute appropriately.
        """
        if '_id' not in kwargs:
            password = kwargs.get('password')
            kwargs.update(
                {
                    'password': self.release_password(password),
                    'chats': [],
                    'contacts': []
                }
            )
        super().__init__(**kwargs)

    @classmethod
    def get_user(cls, username):
        user_doc = cls.collection.find_one({'username': username})
        if user_doc:
            return cls(**user_doc)

    def set_auth_state(self, state):
        self.update(is_authenticate=state)

    def release_password(self, password):
        return pbkdf2_hmac(
            'sha256', password.encode(), SALT.encode(), 100000
        ).hex()

    def check_password(self, password):
        return self.release_password(password) == self.password

    def get_contacts(self):
        result = self.collection.aggregate(
            [
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'contacts',
                        'foreignField': '_id',
                        'as': 'contacts_objects'
                    }
                },
                {'$match': {'_id': self._id}},
                {'$project': {'_id': 0, 'contacts_objects': 1}},
                {'$unwind': '$contacts_objects'}
            ]
        )
        contacts = [record['contacts_objects'] for record in result]
        return {
            contact['username']: contact['_id'].binary.hex()
            for contact in contacts
        }

    def add_contact(self, contact_id):
        """
        Appends contact_id to 'contacts' array in document
        and to self.contacts attribute.
        """
        self.collection.update_one(
            {'_id': self._id}, {'$push': {'contacts': ObjectId(contact_id)}}
        )
        self.contacts.append(ObjectId(contact_id))

    def remove_contact(self, contact_id):
        """
        Removes contact_id from 'contacts' array in document
        and from self.contacts attribute.
        """
        self.collection.update_one(
            {'_id': self._id}, {'$pull': {'contacts': ObjectId(contact_id)}}
        )
        self.contacts.remove(ObjectId(contact_id))

    def add_chat(self, chat_id):
        """
        Appends chat_id to 'chats' array in document
        and to self.chats attribute.
        """
        self.collection.update_one(
            {'_id': self._id}, {'$push': {'chats': chat_id}}
        )
        self.chats.append(chat_id)

    def remove_chat(self, chat_id):
        """
        Removes chat_id from 'chats' array in document
        and from self.chats attribute.
        """
        self.collection.update_one(
            {'_id': self._id}, {'$pull': {'chat': chat_id}}
        )
        self.chat.remove(chat_id)

    def set_avatar(self):
        self.update(avatar='{}_avatar.png'.format(self.username))

    def delete_avatar(self):
        self.update(avatar=None)


class Chat(Core):

    collection = db.chats

    fields = (
        '_id',
        'chat_type',
        'participants',
        'messages'
    )

    def __init__(self, **kwargs):
        if '_id' not in kwargs:
            kwargs.update({'messages': [], 'participants': []})
        super().__init__(**kwargs)

    @classmethod
    def get_common_chat(cls):
        """
        Returns chat with chat_type field == 'common' if it exists
        or creates such chat and returns it otherwise.
        """
        chat_doc = cls.collection.find_one({'chat_type': 'common'})
        print(chat_doc)
        if not chat_doc:
            return cls(chat_type='common')
        return cls(**chat_doc)

    @classmethod
    def get_single_chat(cls, participants):
        chat_doc = cls.collection.find_one(
            {'participants': {'$all': participants}, 'chat_type': 'single'}
        )
        return cls(**chat_doc)

    def add_participant(self, participant):
        self.collection.update_one(
            {'_id': self._id}, {'$push': {'participants': participant._id}}
        )
        self.participants.append(participant._id)

    def add_message(self, message):
        """Adds message to chat"""
        self.collection.update_one(
            {'_id': self._id}, {'$push': {'messages': message._id}}
        )
        self.messages.append(message._id)

    def get_messages(self):
        result = self.collection.aggregate(
            [
                {
                    '$lookup': {
                        'from': 'messages',
                        'localField': 'messages',
                        'foreignField': '_id',
                        'as': 'message_objects'
                    }
                },
                {'$match': {'_id': self._id}},
                {'$project': {'_id': 0, 'message_objects': 1}},
                {'$unwind': '$message_objects'}
            ]
        )
        result = [
            (
                User.get_by_id(
                    record['message_objects']['sender_id']
                ).username, record['message_objects']['text']
            )
            for record in result
        ]
        return result

    def search_messages(self, text):
        messages = self.get_messages()
        return [
            message for message in messages if re.search(
                text, message[1], flags=re.IGNORECASE
            )
        ]


class Message(Core):

    collection = db.messages

    fields = (
        '_id',
        'sender_id',
        'chat_id',
        'text',
    )
