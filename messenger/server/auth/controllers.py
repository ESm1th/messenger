import logging

from protocol import (
    make_response,
    make_400
)
from db import (
    User,
)


logger = logging.getLogger('server_logger')


def register(request, session):
    user_data = request.get('data')

    if user_data:
        try:
            user = session.query(User).filter(
                User.username == user_data.get('username') 
            ).one_or_none()

            if not user:
                user = User(**user_data)
                session.add(user)
                session.commit()
                return make_response(request, 200, 'Register completed')
            else:
                return make_response(request, 205, 'Username already exists')

        except Exception as error:
            logger.error(error, exc_info=True)
            return make_response(request, 500, 'Internal server error')

        finally:
            session.close()
    else:
        return make_400(request)


def login(request, session):
    user_data = request.get('data')

    if user_data:
        try:
            user = session.query(User).filter(
                User.username == user_data.get('username')
            ).one_or_none()

            if user:
                if user.password == user_data.get('password'):
                    user.logged = True
                    session.add(user)
                    session.commit()
                    return make_response(request, 200, 'User logged in')
                else:
                    return make_response(request, 205, 'Wrong password')
            else:
                return make_response(request, 205, 'Username does not exists')

        except Exception as error:
            logger.error(error, exc_info=True)
            return make_response(request, 500, 'Internal server error')

        finally:
            session.close()

    else:
        return make_400(request)