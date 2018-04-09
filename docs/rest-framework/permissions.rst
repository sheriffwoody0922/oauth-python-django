Permissions
===========

Django OAuth Toolkit provides a few utility classes to use along with other permissions in Django REST Framework,
so you can easily add scoped-based permission checks to your API views.

More details on how to add custom permissions to your API Endpoints can be found at the official
`Django REST Framework documentation <http://www.django-rest-framework.org/api-guide/permissions/>`_


TokenHasScope
-------------

The `TokenHasScope` permission class allows access only when the current access token has been
authorized for **all** the scopes listed in the `required_scopes` field of the view.

For example:

.. code-block:: python

    class SongView(views.APIView):
        authentication_classes = [OAuth2Authentication]
        permission_classes = [TokenHasScope]
        required_scopes = ['music']

The `required_scopes` attribute is mandatory.


TokenHasReadWriteScope
----------------------

The `TokenHasReadWriteScope` permission class allows access based on the `READ_SCOPE` and `WRITE_SCOPE` configured in the settings.

When the current request's method is one of the "safe" methods `GET`, `HEAD`, `OPTIONS`
the access is allowed only if the access token has been authorized for the `READ_SCOPE` scope.
When the request's method is one of `POST`, `PUT`, `PATCH`, `DELETE` the access is allowed if the access token has been authorized for the `WRITE_SCOPE`.

The `required_scopes` attribute is optional and can be used by other scopes needed in the view.

For example:

.. code-block:: python

    class SongView(views.APIView):
        authentication_classes = [OAuth2Authentication]
        permission_classes = [TokenHasReadWriteScope]
        required_scopes = ['music']

When a request is performed both the `READ_SCOPE` \\ `WRITE_SCOPE` and 'music' scopes are required to be authorized for the current access token.

TokenHasResourceScope
----------------------
The `TokenHasResourceScope` permission class allows access only when the current access token has been authorized for **all** the scopes listed in the `required_scopes` field of the view but according of request's method.

When the current request's method is one of the "safe" methods, the access is allowed only if the access token has been authorized for the `scope:read` scope (for example `music:read`).
When the request's method is one of "non safe" methods, the access is allowed only if the access token has been authorized for the `scope:write` scope (for example `music:write`).

.. code-block:: python

    class SongView(views.APIView):
        authentication_classes = [OAuth2Authentication]
        permission_classes = [TokenHasResourceScope]
        required_scopes = ['music']

The `required_scopes` attribute is mandatory (you just need inform the resource scope).


IsAuthenticatedOrTokenHasScope
------------------------------
The `IsAuthenticatedOrTokenHasScope` permission class allows access only when the current access token has been authorized for **all** the scopes listed in the `required_scopes` field of the view but according to the request's method.
It also allows access to Authenticated users who are authenticated in django, but were not authenticated through the OAuth2Authentication class.
This allows for protection of the API using scopes, but still let's users browse the full browseable API.
To restrict users to only browse the parts of the browseable API they should be allowed to see, you can combine this with the DjangoModelPermission or the DjangoObjectPermission.

For example:

.. code-block:: python

    class SongView(views.APIView):
        permission_classes = [IsAuthenticatedOrTokenHasScope, DjangoModelPermission]
        required_scopes = ['music']

The `required_scopes` attribute is mandatory.
