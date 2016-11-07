# pylint: disable=missing-docstring
from functools import wraps
from flask import request, Response

from research_app.application import app


def check_auth(auth):
    ''' This function is called to check if a username/password combination
    is valid.
    '''
    return auth.username == app.config['AUTH_USERNAME'] and \
           auth.password == app.config['AUTH_PASSWORD']


def authenticate():
    ''' Sends a 401 response that enables basic auth.
    '''
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth):
            return authenticate()
        return func(*args, **kwargs)
    return decorated
