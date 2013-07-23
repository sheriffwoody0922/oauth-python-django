from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from ..models import get_application_model


Application = get_application_model()


class BaseTest(TestCase):
    def setUp(self):
        self.foo_user = User.objects.create_user("foo_user", "test@user.com", "123456")
        self.bar_user = User.objects.create_user("bar_user", "dev@user.com", "123456")

    def tearDown(self):
        self.foo_user.delete()
        self.bar_user.delete()


class TestApplicationRegistrationView(BaseTest):
    def test_application_registration_user(self):
        self.client.login(username="foo_user", password="123456")

        form_data = {
            'name': 'Foo app',
            'client_id': 'client_id',
            'client_secret': 'client_secret',
            'client_type': Application.CLIENT_CONFIDENTIAL,
            'redirect_uris': 'http://example.com',
            'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE
        }

        response = self.client.post(reverse('oauth2_provider:register'), form_data)
        self.assertEqual(response.status_code, 302)

        app = Application.objects.get(name="Foo app")
        self.assertEqual(app.user.username, "foo_user")


class TestApplicationViews(BaseTest):
    def _create_application(self, name, user):
        app = Application.objects.create(
            name=name, redirect_uris="http://example.com",
            client_type=Application.CLIENT_CONFIDENTIAL, authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            user=user)
        return app

    def setUp(self):
        super(TestApplicationViews, self).setUp()
        self.app_foo_1 = self._create_application('app foo_user 1', self.foo_user)
        self.app_foo_2 = self._create_application('app foo_user 2', self.foo_user)
        self.app_foo_3 = self._create_application('app foo_user 3', self.foo_user)

        self.app_bar_1 = self._create_application('app bar_user 1', self.bar_user)
        self.app_bar_2 = self._create_application('app bar_user 2', self.bar_user)

    def tearDown(self):
        super(TestApplicationViews, self).tearDown()
        Application.objects.all().delete()

    def test_application_list(self):
        self.client.login(username="foo_user", password="123456")

        response = self.client.get(reverse('oauth2_provider:list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)

    def test_application_detail_owner(self):
        self.client.login(username="foo_user", password="123456")

        response = self.client.get(reverse('oauth2_provider:detail', args=(self.app_foo_1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_application_detail_not_owner(self):
        self.client.login(username="foo_user", password="123456")

        response = self.client.get(reverse('oauth2_provider:detail', args=(self.app_bar_1.pk,)))
        self.assertEqual(response.status_code, 404)
