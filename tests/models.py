from django.db import models

from oauth2_provider.settings import oauth2_settings
from oauth2_provider.models import (
    AbstractAccessToken, AbstractApplication,
    AbstractGrant, AbstractRefreshToken
)


class BaseTestApplication(AbstractApplication):
    allowed_schemes = models.TextField(blank=True)

    def get_allowed_schemes(self):
        if self.allowed_schemes:
            return self.allowed_schemes.split()
        return super(BaseTestApplication, self).get_allowed_schemes()


class SampleApplication(AbstractApplication):
    custom_field = models.CharField(max_length=255)


class SampleAccessToken(AbstractAccessToken):
    custom_field = models.CharField(max_length=255)
    source_refresh_token = models.OneToOneField(
        # unique=True implied by the OneToOneField
        oauth2_settings.REFRESH_TOKEN_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="s_refreshed_access_token"
    )


class SampleRefreshToken(AbstractRefreshToken):
    custom_field = models.CharField(max_length=255)
    access_token = models.OneToOneField(
        oauth2_settings.ACCESS_TOKEN_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="s_refresh_token"
    )


class SampleGrant(AbstractGrant):
    custom_field = models.CharField(max_length=255)
