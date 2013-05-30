from django.core.exceptions import ImproperlyConfigured
from django.views.generic import View
from django.test import TestCase, RequestFactory

from oauthlib.oauth2 import Server

from ..mixins import OAuthLibMixin
from ..oauth2_validators import OAuth2Validator


class TestOAuthLibMixin(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request_factory = RequestFactory()

    def test_missing_server_class(self):
        class TestView(OAuthLibMixin, View):
            validator_class = OAuth2Validator

        request = self.request_factory.get("/fake-req")
        test_view = TestView()

        self.assertRaises(ImproperlyConfigured, test_view.get_server, request)

    def test_missing_validator_class(self):
        class TestView(OAuthLibMixin, View):
            server_class = Server

        request = self.request_factory.get("/fake-req")
        test_view = TestView()

        self.assertRaises(ImproperlyConfigured, test_view.get_server, request)

    def test_correct_server(self):
        class TestView(OAuthLibMixin, View):
            server_class = Server
            validator_class = OAuth2Validator

        request = self.request_factory.get("/fake-req")
        request.user = "fake"
        test_view = TestView()

        self.assertIsInstance(test_view.get_server(request), Server)
