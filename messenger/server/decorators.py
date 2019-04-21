import logging
import inspect
from functools import wraps
from protocol import make_403

logger = logging.getLogger('server_logger')


def logged(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        caller = inspect.stack()[1].function
        logger.debug(f'{ func.__name__ } { request }')
        logger.debug(
            f'Function "{ func.__name__ }" called from function "{ caller }"'
        )
        return func(request, *args, **kwargs)
    return wrapper


def login_required(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        user = request.get('user')
        if user:
            return func(request, *args, **kwargs)
        
        return make_403(request)
    
    return wrapper
