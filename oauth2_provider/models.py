from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _

from .generators import generate_client_secret, generate_client_id
from .validators import validate_uris


class Application(models.Model):
    """
    An Application instance represents a Client on the Authorization server. Usually an Application is created
    manually by client's developers after logging in on an Authorization Server.

    Fields:

    * :attr:`client_id` The client identifier issued to the client during the registration process as \
    described in :rfc:`2.2`
    * :attr:`user` ref to a Django user
    * :attr:`redirect_uris` The list of allowed redirect uri. The string consists of valid URLs separated by space
    * :attr:`client_type` Client type as described in :rfc:`2.1`
    * :attr:`authorization_grant_type` Authorization flows available to the Application
    * :attr:`client_secret` Confidential secret issued to the client during the registration process as \
    described in :rfc:`2.2`
    * :attr:`name` Friendly name for the Application
    """
    CLIENT_CONFIDENTIAL = 'confidential'
    CLIENT_PUBLIC = 'public'
    CLIENT_TYPES = (
        (CLIENT_CONFIDENTIAL, _('Confidential')),
        (CLIENT_PUBLIC, _('Public')),
    )

    GRANT_ALLINONE = 'all-in-one'
    GRANT_AUTHORIZATION_CODE = 'authorization-code'
    GRANT_IMPLICIT = 'implicit'
    GRANT_PASSWORD = 'password'
    GRANT_CLIENT_CREDENTIAL = 'client-credential'
    GRANT_TYPES = (
        (GRANT_ALLINONE, _('All-in-one generic')),
        (GRANT_AUTHORIZATION_CODE, _('Authorization code')),
        (GRANT_IMPLICIT, _('Implicit')),
        (GRANT_PASSWORD, _('Resource owner password-based')),
        (GRANT_CLIENT_CREDENTIAL, _('Client credentials')),
    )

    client_id = models.CharField(max_length=100, unique=True, default=generate_client_id)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    redirect_uris = models.TextField(help_text=_("Allowed URIs list space separated"), validators=[validate_uris])
    client_type = models.CharField(max_length=32, choices=CLIENT_TYPES)
    authorization_grant_type = models.CharField(max_length=32, choices=GRANT_TYPES)
    client_secret = models.CharField(max_length=255, blank=True, default=generate_client_secret)
    name = models.CharField(max_length=255, blank=True)

    @property
    def default_redirect_uri(self):
        """
        Returns the default redirect_uri extracting the first item from the :attr:`redirect_uris` string
        """
        return self.redirect_uris.split().pop(0)

    def redirect_uri_allowed(self, uri):
        """
        Checks if given url is one of the items in :attr:`redirect_uris` string
        """
        uri = uri.rstrip("/")
        return uri in self.redirect_uris.split()

    def __unicode__(self):
        return self.client_id


class Grant(models.Model):
    """
    A Grant instance represents a token with a short lifetime that can be swapped for an access token, as described
    in :rfc:`4.1.2`

    Fields:

    * :attr:`user` The Django user who requested the grant
    * :attr:`code` The authorization code generated by the authorization server
    * :attr:`application` Application instance this grant was asked for
    * :attr:`expires` Expire time in seconds, defaults to :data:`settings.AUTHORIZATION_CODE_EXPIRE_SECONDS`
    * :attr:`redirect_uri` Self explained
    * :attr:`scope` Requested scopes, optional
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    code = models.CharField(max_length=255)  # code comes from oauthlib
    application = models.ForeignKey(Application)
    expires = models.DateTimeField()
    redirect_uri = models.CharField(max_length=255)
    scope = models.TextField(blank=True)

    def is_expired(self):
        return timezone.now() >= self.expires

    def redirect_uri_allowed(self, uri):
        return uri == self.redirect_uri.rstrip("/")

    def __unicode__(self):
        return self.code


class AccessToken(models.Model):
    """
    An AccessToken instance represents the actual access token to access user's resources, as in :rfc:`5`.

    Fields:

    * :attr:`user` The Django user representing resources' owner
    * :attr:`token` Access token
    * :attr:`application` Application instance
    * :attr:`expires` Expire time in seconds, defaults to :data:`settings.ACCESS_TOKEN_EXPIRE_SECONDS`
    * :attr:`scope` Allowed scopes
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    token = models.CharField(max_length=255)  # TODO generate code
    application = models.ForeignKey(Application)
    expires = models.DateTimeField()  # TODO provide a default value based on the settings
    scope = models.TextField(blank=True)

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.
        """
        return not self.is_expired() and self.allow_scopes(scopes)

    def is_expired(self):
        return timezone.now() >= self.expires

    def allow_scopes(self, scopes):
        """
        Check if the token allows the provided scopes

        Params:

        * :attr:`scopes` A string containing the scopes to check
        """
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)

    def __unicode__(self):
        return self.token


class RefreshToken(models.Model):
    """
    A RefreshToken instance represents a token that can be swapped for a new access token when it expires.

    Fields:

    * :attr:`user` The Django user representing resources' owner
    * :attr:`token` Token value
    * :attr:`application` Application instance
    * :attr:`access_token` AccessToken instance this refresh token is bounded to
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    token = models.CharField(max_length=255)  # TODO generate code
    application = models.ForeignKey(Application)
    access_token = models.OneToOneField(AccessToken, related_name='refresh_token')

    def __unicode__(self):
        return self.token
