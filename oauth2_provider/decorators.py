from functools import wraps

from oauthlib.oauth2 import Server
from django.http import HttpResponseForbidden
from django.core.exceptions import ImproperlyConfigured

from .oauth2_validators import OAuth2Validator
from .backends import OAuthLibCore
from .settings import oauth2_settings


def protected_resource(view_func, scopes=None, validator_cls=OAuth2Validator, server_cls=Server):
    """
    Decorator to protect views by providing OAuth2 authentication out of the box, optionally with scope handling.
    """
    if scopes is None:
        scopes = []
    
    @wraps(view_func)
    def _validate(request, *args, **kwargs):
        validator = validator_cls()
        core = OAuthLibCore(server_cls(validator))
        valid, oauthlib_req = core.verify_request(request, scopes=scopes)
        if valid:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden()
    return _validate


def rw_protected_resource(view_func, scopes=None, validator_cls=OAuth2Validator, server_cls=Server):
    """
    Decorator to protect views by providing OAuth2 authentication and read/write scopes out of the box.
    GET, HEAD, OPTIONS http methods require "read" scope. Otherwise "write" scope is required.
    """
    if scopes is None:
        scopes = []

    @wraps(view_func)
    def _validate(request, *args, **kwargs):
        # Check if provided scopes are acceptable
        provided_scopes = oauth2_settings._SCOPES
        read_write_scopes = [oauth2_settings.READ_SCOPE, oauth2_settings.WRITE_SCOPE]

        if not set(read_write_scopes).issubset(set(provided_scopes)):
            raise ImproperlyConfigured(
                "rw_protected_resource decorator requires following scopes {0}"
                " to be in OAUTH2_PROVIDER['SCOPES'] list in settings".format(read_write_scopes)
            )

        # Check if method is safe
        if request.method.upper() in ['GET', 'HEAD', 'OPTIONS']:
            scopes.append(oauth2_settings.READ_SCOPE)
        else:
            scopes.append(oauth2_settings.WRITE_SCOPE)

        # proceed with validation
        validator = validator_cls()
        core = OAuthLibCore(server_cls(validator))
        valid, oauthlib_req = core.verify_request(request, scopes=scopes)
        if valid:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden()
    return _validate
