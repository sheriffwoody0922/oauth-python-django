from __future__ import unicode_literals

import logging

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseForbidden

from ..backends import OAuthLibCore
from ..exceptions import FatalClientError
from ..settings import oauth2_settings


log = logging.getLogger("oauth2_provider")

SAFE_HTTP_METHODS = ['GET', 'HEAD', 'OPTIONS']


class OAuthLibMixin(object):
    """
    This mixin decouples Django OAuth Toolkit from OAuthLib.
    """
    server_class = None
    validator_class = None

    def get_server_class(self):
        """
        Return the OAuthlib server class to use
        """
        if self.server_class is None:
            raise ImproperlyConfigured(
                "OAuthLibMixin requires either a definition of 'server_class'"
                " or an implementation of 'get_server_class()'")
        else:
            return self.server_class

    def get_validator_class(self):
        """
        Return the RequestValidator implementation class to use
        """
        if self.validator_class is None:
            raise ImproperlyConfigured(
                "OAuthLibMixin requires either a definition of 'validator_class'"
                " or an implementation of 'get_validator_class()'")
        else:
            return self.validator_class

    def get_server(self, request):
        """
        Return an instance of `server_class` initialized with a `validator_class`
        object
        """
        server_class = self.get_server_class()
        validator_class = self.get_validator_class()
        return server_class(validator_class(request.user))

    def get_core(self, request):
        server = self.get_server(request)
        return OAuthLibCore(server)

    def validate_authorization_request(self, request):
        """
        A wrapper method that calls validate_authorization_request on `server_class` instance.

        :param request: The current django.http.HttpRequest object
        """
        core = self.get_core(request)
        return core.validate_authorization_request(request)

    def create_authorization_response(self, request, scopes, credentials, allow):
        """
        A wrapper method that calls create_authorization_response on `server_class`
        instance.

        :param request: The current django.http.HttpRequest object
        :param scopes: A space-separated string of provided scopes
        :param credentials: Authorization credentials dictionary containing
                           `client_id`, `state`, `redirect_uri`, `response_type`
        :param allow: True if the user authorize the client, otherwise False
        """
        # TODO: move this scopes conversion from and to string into a utils function
        scopes = scopes.split(" ") if scopes else []

        core = self.get_core(request)
        return core.create_authorization_response(scopes, credentials, allow)

    def create_token_response(self, request):
        """
        A wrapper method that calls create_token_response on `server_class` instance.

        :param request: The current django.http.HttpRequest object
        """
        core = self.get_core(request)
        return core.create_token_response(request)

    def verify_request(self, request):
        """
        A wrapper method that calls verify_request on `server_class` instance.

        :param request: The current django.http.HttpRequest object
        """
        core = self.get_core(request)
        return core.verify_request(request, scopes=self.get_scopes())

    def get_scopes(self):
        """
        This should return the list of scopes required to access the resources. By default it returns an empty list
        """
        return []

    def error_response(self, error, **kwargs):
        """
        Return an error to be displayed to the resource owner if anything goes awry.

        :param error: :attr:`OAuthToolkitError`
        """
        oauthlib_error = error.oauthlib_error
        error_response = {
            'error': oauthlib_error,
            'url': "{0}?{1}".format(oauthlib_error.redirect_uri, oauthlib_error.urlencoded)
        }
        error_response.update(kwargs)

        # If we got a malicious redirect_uri or client_id, we will *not* redirect back to the URL.
        if isinstance(error, FatalClientError):
            redirect = False
        else:
            redirect = True

        return redirect, error_response


class ScopedResourceMixin(object):
    """
    Helper mixin that implements "scopes handling" behaviour
    """
    requested_scopes = None

    def get_scopes(self, *args, **kwargs):
        """
        Return the scopes needed to access the resource

        :param args: Support scopes injections from the outside (not yet implemented)
        """
        if self.requested_scopes is None:
            raise ImproperlyConfigured(
                "ProtectedResourceMixin requires either a definition of 'requested_scopes'"
                " or an implementation of 'get_scopes()'")
        else:
            return self.requested_scopes


class ProtectedResourceMixin(OAuthLibMixin):
    """
    Helper mixin that implements OAuth2 protection on request dispatch, specially useful for Django Generic Views
    """
    def dispatch(self, request, *args, **kwargs):
        valid, r = self.verify_request(request)
        if valid:
            return super(ProtectedResourceMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()


class ReadWriteScopedResourceMixin(ScopedResourceMixin, OAuthLibMixin):
    """
    Helper mixin that implements "read and write scopes" behavior
    """
    requested_scopes = []
    read_write_scope = None

    def __new__(cls, *args, **kwargs):
        provided_scopes = oauth2_settings.SCOPES
        read_write_scopes = [oauth2_settings.READ_SCOPE, oauth2_settings.WRITE_SCOPE]

        if not set(read_write_scopes).issubset(set(provided_scopes)):
            raise ImproperlyConfigured(
                "ReadWriteScopedResourceMixin requires following scopes {0}"
                " to be in OAUTH2_PROVIDER['SCOPES'] list in settings".format(read_write_scopes)
            )

        return super(ReadWriteScopedResourceMixin, cls).__new__(cls, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() in SAFE_HTTP_METHODS:
            self.read_write_scope = oauth2_settings.READ_SCOPE
        else:
            self.read_write_scope = oauth2_settings.WRITE_SCOPE

        return super(ReadWriteScopedResourceMixin, self).dispatch(request, *args, **kwargs)

    def get_scopes(self, *args, **kwargs):
        scopes = super(ReadWriteScopedResourceMixin, self).get_scopes(*args, **kwargs)
        return scopes + [self.read_write_scope]  # this returns a copy so that self.requested_scopes is not modified
