from core import (
    RequestHandler,
    Response,
    Response_400
)
from db import (
    Client,
    Chat
)


class Contacts(RequestHandler):

    model = Client

    def validate_request(self, data):
        """
        Checks if username is not None
        and if it is not empty string
        """

        return bool(data.get('username'))

    def process(self):

        if self.validate_request(self.request.data):
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


class Chat(RequestHandler):

    model = Chat
