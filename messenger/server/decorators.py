import logging
import inspect

logger = logging.getLogger('server_logger')


def logged(func):
    def wrapper(request, *args, **kwargs):
        caller = inspect.stack()[1].function
        logger.debug(f'{ func.__name__ } { request }')
        logger.debug(f'Function "{ func.__name__ }" called from function "{ caller }"')
        return func(request, *args, **kwargs)
    return wrapper
