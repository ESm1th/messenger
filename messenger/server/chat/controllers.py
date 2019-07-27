from bson import ObjectId

from core import (
    RequestHandler,
    Response,
)
from mongo import (
    User,
    Chat,
    Message,
)


class AddContact(RequestHandler):

    model = User

    def process(self):

        if self.validate_request():
            user = self.model.get_user(
                self.request.data.get('username')
            )

            contact = self.model.get_user(
                self.request.data.get('contact')
            )

            if contact:
                if contact._id in user.contacts:
                    return Response(
                        self.request,
                        data={
                            'code': 205,
                            'info': 'User already in your contact list.'
                        }
                    )
                else:
                    user.add_contact(contact.id)
                    return Response(
                        self.request,
                        data={
                            'info': 'User was added to your contact list',
                            'new_contact': {
                                contact.username: contact.id
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


class DeleteContact(RequestHandler):

    model = User

    def process(self):

        if self.validate_request():
            user = self.model.get_user(self.request.data.get('username'))
            contact_id = self.request.data.get('contact_id')
            user.remove_contact(contact_id)

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


class GetChat(RequestHandler):

    model = User

    def process(self):

        if self.validate_request():
            user = self.model.get_user(self.request.data.get('username'))

            contact = self.model.get_by_id(
                self.request.data.get('contact_id')
            )

            participants = [user._id, contact._id]
            chat = Chat.get_single_chat(participants)

            if not chat:
                chat = Chat(participants=participants, chat_type='single')

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

                messages = chat.get_messages()
                response.data.update(
                    {'messages': messages, 'lenght': len(messages)}
                )

            return response


class CommonChat(RequestHandler):

    model = Chat

    def process(self):

        if self.validate_request():

            common_chat = self.model.get_common_chat()
            user = User.get_user(self.request.data.get('username'))

            data = {
                'code': 200,
                'chat_id': common_chat.id,
            }

            if common_chat.messages:
                messages = common_chat.get_messages()
                data.update(
                    {'messages': messages, 'lenght': len(messages)}
                )

            if user._id not in common_chat.participants:
                common_chat.add_participant(user)

            return Response(self.request, data=data)


class AddMessage(RequestHandler):

    model = Chat

    def process(self):

        if self.validate_request():

            chat = self.model.get_by_id(self.request.data.get('chat_id'))
            message = Message(
                sender_id=ObjectId(self.request.data.get('user_id')),
                chat_id=chat._id,
                text=self.request.data.get('message')
            )
            chat.add_message(message)

            return Response(
                self.request,
                data={
                    'code': 200,
                    'info': 'Message has been added to database',
                    'chat_id': chat.id,
                    'contact_username': self.request.data.get(
                        'contact_username'
                    ),
                    'message': (
                        self.request.data.get('username'), message.text
                    )
                }
            )


class Profile(RequestHandler):

    model = User

    def process(self):

        if self.validate_request():

            user = self.model.get_user(self.request.data.get('username'))

            user_data = {
                'first_name': getattr(user, 'first_name', None),
                'second_name': getattr(user, 'second_name', None),
                'bio': getattr(user, 'bio', None),
            }

            avatar = getattr(user, 'avatar', None)
            if avatar:
                user_data.update({'file_name': avatar})

            return Response(
                self.request,
                data={
                    'code': 200,
                    'info': 'Profile data were retrieved from database',
                    'user_data': user_data,
                }
            )


class UpdateProfile(RequestHandler):

    model = User

    def process(self):

        if self.validate_request():

            user = self.model.get_user(self.request.data.pop('username'))
            status = self.request.data.pop('upload_status', None)

            if status:

                if hasattr(user, 'avatar'):
                    user.delete_avatar()
                user.set_avatar()

            user.update(**self.request.data)

            return Response(
                self.request,
                data={
                    'code': 200,
                    'info': 'Profile data were retrieved from database',
                    'user_data': {
                        'first_name': getattr(user, 'first_name', None),
                        'second_name': getattr(user, 'second_name', None),
                        'bio': getattr(user, 'bio', None),
                        'file_name': getattr(user, 'avatar', None)
                    }
                }
            )


class SearchInChat(RequestHandler):

    model = Chat

    def process(self):

        if self.validate_request():

            chat = self.model.get_by_id(self.request.data.get('chat_id'))
            messages = chat.search_messages(self.request.data.get('word'))

            return Response(
                self.request,
                data={
                    'code': 200,
                    'info': 'Messages were retrived from database' if messages
                    else 'Found zero messages',
                    'messages': messages
                }
            )
