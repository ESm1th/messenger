import logging
import base64

from core import (
    RequestHandler,
    Response,
    Response_400,
)
from db import (
    Client,
    ClientHistory,
    SessionScope
)


logger = logging.getLogger('server_logger')


class AuthBase(RequestHandler):
    """Base class for [auth] app controllers"""

    model = Client

    def validate_request(self, data):
        """
        Checks if username and password are not None
        and if they are not empty string
        """
        print('in validate')
        username = data.get('username')

        if username != '' and username:
            password = data.get('password')

            if password != '' and password:
                return True

        return False


class Register(AuthBase):
    """Class for register new user"""

    def validate_request(self, data):
        """Adds validation of passwords equalent"""

        if super().validate_request(data):
            password = data.get('password')
            if password == data.get('repeat_password'):
                return True
        return False

    def process(self):
        """
        Creates new user if requests data is valid and
        user does not exist in database
        """

        if self.validate_request(self.request.data):
            self.request.data.pop('repeat_password')
            username = self.request.data.get('username')
            user = self.model.get_client(self.session, username)

            if not user:
                self.model.create(self.session, **self.request.data)
                return Response(self.request, {'info': 'Register completed'})
            else:
                return Response(
                    self.request,
                    {'code': 205, 'info': 'Clientname already exists'}
                )
        else:
            return Response_400(self.request)


class Login(AuthBase):
    """Class for loggining user"""

    def process(self):
        if self.validate_request(self.request.data):
            username = self.request.data.get('username')
            user = self.model.get_client(self.session, username)

            if user:
                password = self.request.data.get('password')

                if password == user.password:

                    contacts = {
                        contact.user.username: contact.id
                        for contact in user.contacts
                    }

                    user.set_auth_state(self.session, True)
                    user.add_address(
                        self.session,
                        str(self.request.data.get('address'))
                    )

                    user_data = {
                        'username': user.username,
                        'user_id': user.id,
                        'contacts': contacts,                        
                    }

                    avatar = user.get_avatar(self.session)

                    if avatar:
                        image = self.image_prepare(avatar.path)
                        user_data.update({'avatar': image})

                    return Response(
                        self.request,
                        data={
                            'code': 200,
                            'info': 'Client logged in',
                            'user_data': user_data
                        }
                    )
                else:
                    return Response(
                        self.request,
                        {'code': 205, 'info': 'Wrong password'}
                    )
            else:
                return Response(
                    self.request,
                    {'code': 205, 'info': 'Username does not exists'}
                )
        else:
            return Response_400(self.request)
    
    def image_prepare(self, path):
        with open(path, 'rb') as file:
            image = file.read()

        encoded_image = base64.b64encode(image)
        return encoded_image.decode('utf-8')


class Logout(AuthBase):

    def validate_request(self, data):
        return bool(data.get('username'))

    def process(self):

        if self.validate_request(self.request.data):

            username = self.request.data.get('username')
            user = self.model.get_client(self.session, username)

            if user:
                user.set_auth_state(self.session, False)

                return Response(
                    self.request, {
                        'code': 200,
                        'info': 'Client logged out',
                        'username': user.username,
                        'user_id': user.id,
                    }
                )
