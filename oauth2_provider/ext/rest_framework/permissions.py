import logging

from django.core.exceptions import ImproperlyConfigured

from rest_framework.permissions import BasePermission

from ...settings import oauth2_settings


log = logging.getLogger('oauth2_provider')

SAFE_HTTP_METHODS = ['GET', 'HEAD', 'OPTIONS']


class TokenHasScope(BasePermission):
    """
    The request is authenticated as a user and the token used has the right scope
    """

    def has_permission(self, request, view):
        token = request.auth

        if not token:
            return False

        if hasattr(token, 'scope'):  # OAuth 2
            required_scopes = self.get_scopes(request, view)
            log.debug("Required scopes to access resource: {0}".format(required_scopes))

            return token.is_valid(required_scopes)

        assert False, ('TokenHasScope requires either the'
                       '`oauth2_provider.rest_framework.OAuth2Authentication` authentication '
                       'class to be used.')

    def get_scopes(self, request, view):
        if not hasattr(view, 'get_scopes'):
            raise ImproperlyConfigured(
                'TokenHasScope requires either the view to inherit oauth2_provider.views.mixins.ScopedResourceMixin '
                'or implement get_scopes method')

        return view.get_scopes()


class TokenHasReadWriteScope(TokenHasScope):
    """
    The request is authenticated as a user and the token used has the right scope
    """

    def get_scopes(self, request, view):
        try:
            required_scopes = super(TokenHasReadWriteScope, self).get_scopes(request, view)
        except ImproperlyConfigured:
            required_scopes = []

        # TODO: code duplication!! see dispatch in ReadWriteScopedResourceMixin
        if request.method.upper() in SAFE_HTTP_METHODS:
            read_write_scope = oauth2_settings.READ_SCOPE
        else:
            read_write_scope = oauth2_settings.WRITE_SCOPE

        return required_scopes + [read_write_scope]
