from __future__ import unicode_literals

import json

from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.utils import timezone

from ..compat import urlparse, parse_qs, urlencode, get_user_model
from ..models import Application, Grant
from ..settings import oauth2_settings
from ..views import ProtectedResourceView

from .test_utils import TestCaseUtils


# mocking a protected resource view
class ResourceView(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        return "This is a protected resource"


class BaseTest(TestCaseUtils, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.test_user = get_user_model().objects.create_user("test_user", "test@user.com", "123456")
        self.dev_user = get_user_model().objects.create_user("dev_user", "dev@user.com", "123456")

        self.application = Application(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.dev_user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        self.application.save()

        oauth2_settings.SCOPES = ['read', 'write']

    def tearDown(self):
        self.application.delete()
        self.test_user.delete()
        self.dev_user.delete()


class TestAuthorizationCodeView(BaseTest):
    def test_pre_auth_invalid_client(self):
        """
        Test error for an invalid client_id with response_type: code
        """
        self.client.login(username="test_user", password="123456")

        query_string = urlencode({
            'client_id': 'fakeclientid',
            'response_type': 'code',
        })
        url = "{url}?{qs}".format(url=reverse('authorize'), qs=query_string)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_pre_auth_valid_client(self):
        """
        Test response for a valid client_id with response_type: code
        """
        self.client.login(username="test_user", password="123456")

        query_string = urlencode({
            'client_id': self.application.client_id,
            'response_type': 'code',
            'state': 'random_state_string',
            'scope': 'read write',
            'redirect_uri': 'http://example.it',
        })
        url = "{url}?{qs}".format(url=reverse('authorize'), qs=query_string)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # check form is in context and form params are valid
        self.assertIn("form", response.context)

        form = response.context.get("form")
        self.assertEqual(form['redirect_uri'].value(), "http://example.it")
        self.assertEqual(form['state'].value(), "random_state_string")
        self.assertEqual(form['scopes'].value(), "read write")
        self.assertEqual(form['client_id'].value(), self.application.client_id)

    def test_pre_auth_default_redirect(self):
        """
        Test for default redirect uri if omitted from query string with response_type: code
        """
        self.client.login(username="test_user", password="123456")

        query_string = urlencode({
            'client_id': self.application.client_id,
            'response_type': 'code',
        })
        url = "{url}?{qs}".format(url=reverse('authorize'), qs=query_string)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        form = response.context.get("form")
        self.assertEqual(form['redirect_uri'].value(), "http://localhost")

    def test_pre_auth_forbibben_redirect(self):
        """
        Test error when passing a forbidden redirect_uri in query string with response_type: code
        """
        self.client.login(username="test_user", password="123456")

        query_string = urlencode({
            'client_id': self.application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://forbidden.it',
        })
        url = "{url}?{qs}".format(url=reverse('authorize'), qs=query_string)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_pre_auth_wrong_response_type(self):
        """
        Test error when passing a wrong response_type in query string
        """
        self.client.login(username="test_user", password="123456")

        query_string = urlencode({
            'client_id': self.application.client_id,
            'response_type': 'WRONG',
        })
        url = "{url}?{qs}".format(url=reverse('authorize'), qs=query_string)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("error=unauthorized_client", response['Location'])

    def test_code_post_auth_allow(self):
        """
        Test authorization code is given for an allowed request with response_type: code
        """
        self.client.login(username="test_user", password="123456")

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://example.it',
            'response_type': 'code',
            'allow': True,
        }

        response = self.client.post(reverse('authorize'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://example.it/?', response['Location'])
        self.assertIn('state=random_state_string', response['Location'])
        self.assertIn('code=', response['Location'])

    def test_code_post_auth_deny(self):
        """
        Test error when resource owner deny access
        """
        self.client.login(username="test_user", password="123456")

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://example.it',
            'response_type': 'code',
            'allow': False,
        }

        response = self.client.post(reverse('authorize'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("error=access_denied", response['Location'])

    def test_code_post_auth_bad_responsetype(self):
        """
        Test authorization code is given for an allowed request with a response_type not supported
        """
        self.client.login(username="test_user", password="123456")

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://example.it',
            'response_type': 'UNKNOWN',
            'allow': True,
        }

        response = self.client.post(reverse('authorize'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://example.it/?error', response['Location'])

    def test_code_post_auth_forbidden_redirect_uri(self):
        """
        Test authorization code is given for an allowed request with a forbidden redirect_uri
        """
        self.client.login(username="test_user", password="123456")

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://forbidden.it',
            'response_type': 'code',
            'allow': True,
        }

        response = self.client.post(reverse('authorize'), data=form_data)
        self.assertEqual(response.status_code, 400)


class TestAuthorizationCodeTokenView(BaseTest):
    def get_auth(self):
        """
        Helper method to retrieve a valid authorization code
        """
        authcode_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://example.it',
            'response_type': 'code',
            'allow': True,
        }

        response = self.client.post(reverse('authorize'), data=authcode_data)
        query_dict = parse_qs(urlparse(response['Location']).query)
        return query_dict['code'].pop()

    def test_basic_auth(self):
        """
        Request an access token using basic authentication for client authentication
        """
        self.client.login(username="test_user", password="123456")
        authorization_code = self.get_auth()

        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://example.it'
        }
        auth_headers = self.get_basic_auth_header(self.application.client_id, self.application.client_secret)

        response = self.client.post(reverse('token'), data=token_request_data, **auth_headers)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content['token_type'], "Bearer")
        self.assertEqual(content['scope'], "read write")
        self.assertEqual(content['expires_in'], oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

    def test_basic_auth_bad_authcode(self):
        """
        Request an access token using a bad authorization code
        """
        self.client.login(username="test_user", password="123456")

        token_request_data = {
            'grant_type': 'authorization_code',
            'code': 'BLAH',
            'redirect_uri': 'http://example.it'
        }
        auth_headers = self.get_basic_auth_header(self.application.client_id, self.application.client_secret)

        response = self.client.post(reverse('token'), data=token_request_data, **auth_headers)
        self.assertEqual(response.status_code, 400)

    def test_basic_auth_bad_granttype(self):
        """
        Request an access token using a bad grant_type string
        """
        self.client.login(username="test_user", password="123456")

        token_request_data = {
            'grant_type': 'UNKNOWN',
            'code': 'BLAH',
            'redirect_uri': 'http://example.it'
        }
        auth_headers = self.get_basic_auth_header(self.application.client_id, self.application.client_secret)

        response = self.client.post(reverse('token'), data=token_request_data, **auth_headers)
        self.assertEqual(response.status_code, 400)

    def test_basic_auth_grant_expired(self):
        """
        Request an access token using an expired grant token
        """
        self.client.login(username="test_user", password="123456")
        g = Grant(application=self.application, user=self.test_user, code='BLAH', expires=timezone.now(),
                  redirect_uri='', scope='')
        g.save()

        token_request_data = {
            'grant_type': 'authorization_code',
            'code': 'BLAH',
            'redirect_uri': 'http://example.it'
        }
        auth_headers = self.get_basic_auth_header(self.application.client_id, self.application.client_secret)

        response = self.client.post(reverse('token'), data=token_request_data, **auth_headers)
        self.assertEqual(response.status_code, 400)

    def test_basic_auth_bad_secret(self):
        """
        Request an access token using basic authentication for client authentication
        """
        self.client.login(username="test_user", password="123456")
        authorization_code = self.get_auth()

        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://example.it'
        }
        auth_headers = self.get_basic_auth_header(self.application.client_id, 'BOOM!')

        response = self.client.post(reverse('token'), data=token_request_data, **auth_headers)
        self.assertEqual(response.status_code, 400)

    def test_public(self):
        """
        Request an access token using client_type: public
        """
        self.client.login(username="test_user", password="123456")

        self.application.client_type = Application.CLIENT_PUBLIC
        self.application.save()
        authorization_code = self.get_auth()

        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://example.it',
            'client_id': self.application.client_id,
            'client_secret':  self.application.client_secret,
        }

        response = self.client.post(reverse('token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content['token_type'], "Bearer")
        self.assertEqual(content['scope'], "read write")
        self.assertEqual(content['expires_in'], oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)


class TestAuthorizationCodeProtectedResource(BaseTest):
    def test_resource_access_allowed(self):
        self.client.login(username="test_user", password="123456")

        # retrieve a valid authorization code
        authcode_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://example.it',
            'response_type': 'code',
            'allow': True,
        }
        response = self.client.post(reverse('authorize'), data=authcode_data)
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict['code'].pop()

        # exchange authorization code for a valid access token
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://example.it'
        }
        auth_headers = self.get_basic_auth_header(self.application.client_id, self.application.client_secret)

        response = self.client.post(reverse('token'), data=token_request_data, **auth_headers)
        content = json.loads(response.content.decode("utf-8"))
        access_token = content['access_token']

        # use token to access the resource
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token,
        }
        request = self.factory.get("/fake-resource", **auth_headers)
        request.user = self.test_user

        view = ResourceView.as_view()
        response = view(request)
        self.assertEqual(response, "This is a protected resource")

    def test_resource_access_deny(self):
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + "faketoken",
        }
        request = self.factory.get("/fake-resource", **auth_headers)
        request.user = self.test_user

        view = ResourceView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 403)