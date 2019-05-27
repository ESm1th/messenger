from core import (
    RequestHandler,
    Response
)
from db import (
    Client,
    Contact
)


class Contacts(RequestHandler):

    model = Client

    def validate_request(self, data):
        """
        Checks if username is not None
        and if it is not empty string
        """

        username = data.get('username')

        if username != '' and username:
            return True
        else:
            return False

    def process(self):

        if self.validate_request(self.request.data):
            username = self.request.data.get('username')
            user = self.model.get_client(self.session, username)

            if user:
                contacts = Contact.get_contacts(self.session, user)
                if contacts:
                    return Response(
                        self.request, {'code': 202, 'info': contacts}
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
        

