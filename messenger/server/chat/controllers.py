from core import (
    RequestHandler,
    Response,
    Response_400
)
from db import (
    Client,
    Chat,
    Contact,
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


class Chat(ValidateMixin, RequestHandler):

    model = Chat

    def process(self):

        if self.validate_request():

            with SessionScope(self.session) as session:

                user_id = self.request.data.get('username')
                contact_name = self.request.data.get('contact')
                foreign_model = self.model.participants.property.mapper.class_

                participants = session.query(foreign_model).filter(
                    foreign_model.username.in_([user_name, contact_name])
                )

                if participants.count() == 2:
                    chat = session.query(self.model).filter(
                        and_(self.model.participants.contains())
                    ).one_or_none()

                    if not chat:
                        chat = self.model()
                        session.add(chat)
                        session.commit()
                        session.refresh(chat)

                        chat.participants.extend(participants)
                        session.add(chat)
                        session.commit()
                        session.refresh(chat)

                    return Response(
                        self.request,
                        data={
                            'code': 200,
                            'chat_id': chat.id,
                            'messages': chat.messages
                        }
                    )