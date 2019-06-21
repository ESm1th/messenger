from core import (
    RequestHandler,
    Response,
    Response_400
)
from db import (
    Client,
    Chat,
    Contact,
    Message,
    Session,
    SessionScope
)


class ValidateMixin:

    def validate_request(self):
        """
        Checks if username is not None
        and if it is not empty string
        """

        return bool(self.request.data.get('username'))


class Contacts(ValidateMixin, RequestHandler):

    model = Client

    def process(self):

        if self.validate_request():
            username = self.request.data.get('username')
            user = self.model.get_client(self.session, username)

            if user:
                if user.contacts:
                    return Response(
                        self.request, {'code': 202, 'info': user.contacts}
                    )
                else:
                    return Response(
                        self.request, {
                            'code': 202,
                            'info': 'Your contacts list is empty'
                        }
                    )
            else:
                return Response(
                    self.request,
                    {'code': 205, 'info': 'Username does not exists'}
                )
        else:
            return Response_400(self.request)


class AddContact(ValidateMixin, RequestHandler):

    model = Client

    def process(self):

        if self.validate_request():
            user = self.model.get_client(
                Session, self.request.data.get('username')
            )

            contact = self.model.get_client(
                Session, self.request.data.get('contact')
            )

            if contact:
                if contact.id in (con.contact_id for con in user.contacts):
                    return Response(
                        self.request,
                        data={
                            'code': 205,
                            'info': 'User already in your contact list.'
                        }
                    )
                else:
                    with SessionScope(self.session) as session:
                        contact = Contact(
                            owner_id=user.id, contact_id=contact.id
                        )
                        session.add(contact)
                        session.commit()
                        session.refresh(contact)

                        return Response(
                            self.request,
                            data={
                                'info': 'User was added to your contact list',
                                'new_contact': {
                                    contact.user.username: contact.id
                                }
                            }
                        )
            else:
                return Response(
                    self.request,
                    {
                        'code': 205,
                        'info': 'Contact does not exist in database'
                    }
                )


class DeleteContact(ValidateMixin, RequestHandler):

    model = Contact

    def process(self):

        if self.validate_request():

            with SessionScope(self.session) as session:

                contact = session.query(self.model).get(
                    self.request.data.get('contact_id')
                )

                if contact:
                    session.delete(contact)
                    session.commit()

                    return Response(
                        self.request,
                        data={
                                'info': 'Contact has been deleted.',
                                'contact': self.request.data.get('contact')
                            }
                    )
                else:
                    return Response(
                        self.request,
                        {
                            'code': 205,
                            'info': 'Contact does not exist in database'
                        }
                    )


class GetChat(ValidateMixin, RequestHandler):

    def process(self):

        if self.validate_request():

            with SessionScope(self.session) as session:

                user = session.query(Client).get(
                    self.request.data.get('user_id')
                )

                contact = session.query(Contact).get(
                    self.request.data.get('contact_id')
                ).user

                chat = set(user.chats) & set(contact.chats)

                if not chat:
                    chat = Chat()
                    session.add(chat)
                    session.commit()
                    chat.participants.extend([user, contact])
                    session.add(chat)
                    session.commit()
                else:
                    chat = chat.pop()

                response = Response(
                    self.request,
                    data={
                        'code': 200,
                        'chat_id': chat.id,
                        'contact_user_id': contact.id,
                        'contact_username': contact.username,
                        'lenght': 0
                    }
                )

                if chat.messages:

                    messages = [
                        (message.sender_id, message.text) for
                        message in chat.messages
                    ]

                    response.data.update(
                        {'messages': messages, 'lenght': len(messages)}
                    )

                return response


class AddMessage(ValidateMixin, RequestHandler):

    def process(self):

        if self.validate_request():

            with SessionScope(Session) as session:
                message = Message(
                    sender_id=self.request.data.get('user_id'),
                    receiver_id=self.request.data.get('contact_user_id'),
                    chat_id=self.request.data.get('chat_id'),
                    text=self.request.data.get('message')
                )

                session.add(message)
                session.commit()

                return Response(
                    self.request,
                    data={
                        'code': 200,
                        'info': 'Message has been added to database',
                        'chat_id': message.chat_id,
                        'contact_username': self.request.data.get('contact_username'),
                        'message': message.text
                    }
                )


class NewMessageListener(ValidateMixin, RequestHandler):

    def process(self):

        if self.validate_request():

            with SessionScope(Session) as session:
                chat = session.query(Chat).get(
                    self.request.data.get('chat_id')
                )
                lenght = self.request.data.get('lenght')

                if len(chat.messages) > lenght:

                    messages = [
                        (message.sender_id, message.text) for
                        message in chat.messages[lenght:]
                    ]

                    return Response(
                        self.request,
                        data={
                            'code': 200,
                            'info': 'New messages has been added to database',
                            'chat_id': chat.id,
                            'messages': messages,
                            'lenght': len(chat.messages)
                        }
                    )
                else:
                    return Response(
                        self.request,
                        data={
                            'code': 205,
                            'info': 'No new messages',
                        }
                    )
