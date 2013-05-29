import logging
from datetime import timedelta

from django.utils import timezone
from oauthlib.oauth2 import RequestValidator

from .models import Application, Grant, AccessToken, RefreshToken
from .settings import oauth2_settings


log = logging.getLogger('oauth2_provider')

GRANT_TYPE_MAPPING = {
    'authorization_code': (Application.GRANT_ALLINONE, Application.GRANT_AUTHORIZATION_CODE),
    'password': (Application.GRANT_ALLINONE, Application.GRANT_PASSWORD),
    'client_credential': (Application.GRANT_ALLINONE, Application.GRANT_CLIENT_CREDENTIAL),
    'refresh_token': (Application.GRANT_ALLINONE, Application.GRANT_AUTHORIZATION_CODE, Application.GRANT_PASSWORD,
                      Application.GRANT_CLIENT_CREDENTIAL)
}


class OAuth2Validator(RequestValidator):
    def __init__(self, user):
        """
        Inject the user coming from the Django world into the OAuth validator
        """
        self.user = user

    def authenticate_client(self, request, *args, **kwargs):
        """
        Check if client exists and it's authenticating itself as in rfc:`3.2.1`
        """
        auth = request.headers.get('HTTP_AUTHORIZATION', None)

        if not auth:
            return False

        basic, base64 = auth.split(' ')
        client_id, client_secret = base64.decode('base64').split(':')

        try:
            request.client = Application.objects.get(client_id=client_id, client_secret=client_secret)
            return True
        except Application.DoesNotExist:
            return False

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """
        If we are here, the client did not authenticate itself as in rfc:`3.2.1` and we can proceed only if the client
        exists and it's not of type 'Confidential'. Also assign Application instance to request.client.
        """
        try:
            request.client = request.client or Application.objects.get(client_id=client_id)
            return request.client.client_type != Application.CLIENT_CONFIDENTIAL

        except Application.DoesNotExist:
            return False

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        """
        Ensure the redirect_uri is listed in the Application instance redirect_uris field
        """
        grant = Grant.objects.get(code=code, application=client)
        return grant.redirect_uri_allowed(redirect_uri)

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        """
        Remove the temporary grant used to swap the authorization token
        """
        grant = Grant.objects.get(code=code, application=request.client)
        grant.delete()

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """
        Ensure an Application exists with given client_id. Also assign Application instance to request.client.
        """
        try:
            request.client = request.client or Application.objects.get(client_id=client_id)
            return True

        except Application.DoesNotExist:
            return False

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        return request.client.default_redirect_uri

    def validate_bearer_token(self, token, scopes, request):
        try:
            access_token = AccessToken.objects.get(token=token)
            request.user = access_token.user
            return access_token.is_valid(scopes)

        except AccessToken.DoesNotExist:
            return False

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        try:
            grant = Grant.objects.get(code=code, application=client)
            if not grant.is_expired():
                request.user = grant.user
                request.scopes = grant.scope.split(' ')
                return True

        except Grant.DoesNotExist:
            return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """
        Validate both grant_type is a valid string and grant_type is allowed for current workflow
        """
        try:
            return request.client.authorization_grant_type in GRANT_TYPE_MAPPING[grant_type]
        except KeyError:
            return False

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        """
        We currently do not support the Authorization Endpoint Response Types registry as in rfc:`8.4`, so validate
        the response_type only if it matches 'code' or 'token'
        """
        if response_type == 'code':
            return client.authorization_grant_type == Application.GRANT_AUTHORIZATION_CODE
        elif response_type == 'token':
            return client.authorization_grant_type == Application.GRANT_IMPLICIT
        else:
            return False

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """
        Ensure requested scopes are permitted (as specified in the settings file)
        """
        return set(scopes).intersection(set(oauth2_settings.SCOPES))

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        return oauth2_settings.SCOPES

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        return request.client.redirect_uri_allowed(redirect_uri)

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        expires = timezone.now() + timedelta(seconds=oauth2_settings.AUTHORIZATION_CODE_EXPIRE_SECONDS)
        g = Grant(application=request.client, user=self.user, code=code['code'], expires=expires,
                  redirect_uri=request.redirect_uri, scope=' '.join(request.scopes))
        g.save()

    def save_bearer_token(self, token, request, *args, **kwargs):
        expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        access_token = AccessToken(
            user=self.user,  # TODO check why if response_type==token request.user is None
            scope=token['scope'],
            expires=expires,
            token=token['access_token'],
            application=request.client)
        access_token.save()

        if 'refresh_token' in token:
            refresh_token = RefreshToken(
                user=request.user,
                token=token['refresh_token'],
                application=request.client,
                access_token=access_token
            )
            refresh_token.save()

        # TODO check out a more reliable way to communicate expire time to oauthlib
        token['expires_in'] = oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS
