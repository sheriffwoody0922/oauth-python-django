from __future__ import unicode_literals

from django.test import TestCase
from django.urls import reverse

from oauth2_provider.settings import oauth2_settings


class TestConnectDiscoveryInfoView(TestCase):
    def test_get_connect_discovery_info(self):
        expected_response = {
            "issuer": "http://localhost",
            "authorization_endpoint": "http://localhost/o/authorize/",
            "token_endpoint": "http://localhost/o/token/",
            "userinfo_endpoint": "http://localhost/userinfo/",
            "jwks_uri": "http://localhost/o/jwks/",
            "response_types_supported": [
                "code",
                "token",
                "id_token",
                "id_token token",
                "code token",
                "code id_token",
                "code id_token token"
            ],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256", "HS256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"]
        }
        response = self.client.get(reverse("oauth2_provider:oidc-connect-discovery-info"))
        self.assertEqual(response.status_code, 200)
        assert response.json() == expected_response

    def test_get_connect_discovery_info_without_issuer_url(self):
        oauth2_settings.OIDC_ISS_ENDPOINT = None
        oauth2_settings.OIDC_USERINFO_ENDPOINT = None
        expected_response = {
            "issuer": "http://testserver/o",
            "authorization_endpoint": "http://testserver/o/authorize/",
            "token_endpoint": "http://testserver/o/token/",
            "userinfo_endpoint": "http://testserver/o/userinfo/",
            "jwks_uri": "http://testserver/o/jwks/",
            "response_types_supported": [
                "code",
                "token",
                "id_token",
                "id_token token",
                "code token",
                "code id_token",
                "code id_token token"
            ],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256", "HS256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"]
        }
        response = self.client.get(reverse("oauth2_provider:oidc-connect-discovery-info"))
        self.assertEqual(response.status_code, 200)
        assert response.json() == expected_response
        oauth2_settings.OIDC_ISS_ENDPOINT = "http://localhost"
        oauth2_settings.OIDC_USERINFO_ENDPOINT = "http://localhost/userinfo/"


class TestJwksInfoView(TestCase):
    def test_get_jwks_info(self):
        expected_response = {
            "keys": [{
                "alg": "RS256",
                "use": "sig",
                "kid": "s4a1o8mFEd1tATAIH96caMlu4hOxzBUaI2QTqbYNBHs",
                "e": "AQAB",
                "kty": "RSA",
                "n": "mwmIeYdjZkLgalTuhvvwjvnB5vVQc7G9DHgOm20Hw524bLVTk49IXJ2Scw42HOmowWWX-oMVT_ca3ZvVIeffVSN1-TxVy2zB65s0wDMwhiMoPv35z9IKHGMZgl9vlyso_2b7daVF_FQDdgIayUn8TQylBxEU1RFfW0QSYOBdAt8"  # noqa
            }]
        }
        response = self.client.get(reverse("oauth2_provider:jwks-info"))
        self.assertEqual(response.status_code, 200)
        assert response.json() == expected_response
