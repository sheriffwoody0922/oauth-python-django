from __future__ import unicode_literals

try:
    from unittest import skipIf
except ImportError:
    from django.utils.unittest.case import skipIf

import django
from django.test import TestCase
from django.test.utils import override_settings
from django.core.exceptions import ValidationError

from ..models import AccessToken, get_application_model
from ..compat import get_user_model


Application = get_application_model()
UserModel = get_user_model()


class TestModels(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user("test_user", "test@user.com", "123456")

    def test_allow_scopes(self):
        self.client.login(username="test_user", password="123456")
        app = Application(
            name="test_app",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )

        access_token = AccessToken(
            user=self.user,
            scope='read write',
            expires=0,
            token='',
            application=app
        )

        self.assertTrue(access_token.allow_scopes(['read', 'write']))
        self.assertTrue(access_token.allow_scopes(['write', 'read']))
        self.assertTrue(access_token.allow_scopes(['write', 'read', 'read']))
        self.assertTrue(access_token.allow_scopes([]))
        self.assertFalse(access_token.allow_scopes(['write', 'destroy']))

    def test_grant_authorization_code_redirect_uris(self):
        app = Application(
            name="test_app",
            redirect_uris="",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )

        self.assertRaises(ValidationError, app.full_clean)

    def test_grant_implicit_redirect_uris(self):
        app = Application(
            name="test_app",
            redirect_uris="",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_IMPLICIT,
        )

        self.assertRaises(ValidationError, app.full_clean)

    def test_str(self):
        app = Application(
            redirect_uris="",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_IMPLICIT,
        )
        self.assertEqual("%s" % app, app.client_id)

        app.name = "test_app"
        self.assertEqual("%s" % app, "test_app")

@skipIf(django.VERSION < (1, 5), "Behavior is broken on 1.4 and there is no solution")
@override_settings(OAUTH2_PROVIDER_APPLICATION_MODEL='tests.TestApplication')
class TestCustomApplicationModel(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user("test_user", "test@user.com", "123456")

    def test_related_objects(self):
        """
        If a custom application model is installed, it should be present in
        the related objects and not the swapped out one.

        See issue #90 (https://github.com/evonove/django-oauth-toolkit/issues/90)
        """
        # Django internals caches the related objects.
        del UserModel._meta._related_objects_cache
        related_object_names = [ro.name for ro in UserModel._meta.get_all_related_objects()]
        self.assertNotIn('oauth2_provider:application', related_object_names)
        self.assertIn('tests:testapplication', related_object_names)
