from oauthlib.common import CLIENT_ID_CHARACTER_SET, generate_client_id as oauthlib_generate_client_id

from .settings import oauth2_settings


class BaseHashGenerator(object):
    """
    All generators should extend this class overriding `.hash()` method.
    """
    def hash(self):
        raise NotImplementedError()


class ClientIdGenerator(BaseHashGenerator):
    def hash(self):
        """
        Generate a client_id without colon char as in http://tools.ietf.org/html/rfc2617#section-2
        for Basic Authentication scheme
        """
        client_id_charset = CLIENT_ID_CHARACTER_SET.replace(":", "")
        return oauthlib_generate_client_id(length=40, chars=client_id_charset)


class ClientSecretGenerator(BaseHashGenerator):
    def hash(self):
        return oauthlib_generate_client_id(length=128)


def generate_client_id():
    """
    Generate a suitable client id
    """
    client_id_generator = oauth2_settings.CLIENT_ID_GENERATOR_CLASS()
    return client_id_generator.hash()


def generate_client_secret():
    """
    Generate a suitable client secret
    """
    client_secret_generator = oauth2_settings.CLIENT_SECRET_GENERATOR_CLASS()
    return client_secret_generator.hash()
