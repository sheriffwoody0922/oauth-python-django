Getting started
===============

Django OAuth Toolkit provide a support layer for `Django REST Framework <http://django-rest-framework.org/>`_.
This tutorial it's based on the Django REST Framework example and shows you how to easily integrate with it.

Step 1: Minimal setup
----------------------------

Create a virtualenv and install following packages using `pip`...

::

    pip install django-oauth-toolkit djangorestframework

Start a new Django project and add `'rest_framework'` and `'oauth2_provider'` to your `INSTALLED_APPS` setting.

.. code-block:: python

    INSTALLED_APPS = (
        'django.contrib.admin',
        ...
        'oauth2_provider',
        'rest_framework',
    )

Now we need to tell Django REST Framework to use the new authentication backend.
To do so add the following lines add the end of your `settings.py` module:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        )
    }

Step 2: Create a simple API
--------------------------

Let's create a simple API for accessing users and groups.

Here's our project's root `urls.py` module:

.. code-block:: python

    from django.conf.urls.defaults import url, patterns, include
    from django.contrib.auth.models import User, Group
    from django.contrib import admin
    admin.autodiscover()

    from rest_framework import viewsets, routers
    from rest_framework import permissions

    from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope


    # ViewSets define the view behavior.
    class UserViewSet(viewsets.ModelViewSet):
        permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope]
        model = User


    class GroupViewSet(viewsets.ModelViewSet):
        permission_classes = [permissions.IsAuthenticated, TokenHasScope]
        required_scopes = ['groups']
        model = Group


    # Routers provide an easy way of automatically determining the URL conf
    router = routers.DefaultRouter()
    router.register(r'users', UserViewSet)
    router.register(r'groups', GroupViewSet)


    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browseable API.
    urlpatterns = patterns('',
        url(r'^', include(router.urls)),
        url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
        url(r'^admin/', include(admin.site.urls)),
    )

Also add the following to your `settings.py` module:

.. code-block:: python

    OAUTH2_PROVIDER = {
        # this is the list of available scopes
        'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
    }

    REST_FRAMEWORK = {
        # ...

        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated',
        )
    }

`OAUTH2_PROVIDER.SCOPES` parameter contains the scopes that the application will be aware of,
so we can use them for permission check.

Now run `python manage.py syncdb`, login to admin and create some users and groups.

Step 3: Register an application
-------------------------------

To obtain a valid access_token first we must register an application. DOT has a set of customizable
views you can use to CRUD application instances, just point your browser at:

    `http://localhost:8000/o/applications/`

Click the button `New Application` and fill the form with the following data:

* User: *your current user*
* Client Type: *confidential*
* Authorization Grant Type: *Resource owner password-based*

Save your app!

Step 4: Get your token and use your API
---------------------------------------

At this point we're ready to request an access_token. Open your shell

::

    curl -X POST -d "grant_type=password&username=<user_name>&password=<password>" http://<client_id>:<client_secret>@localhost:8000/o/token/

The *user_name* and *password* are the credential on any user registered in your :term:`Authorization Server`, like any user created in Step 2.
Response should be something like:

.. code-block:: javascript

    {
        "access_token": "<your_access_token>",
        "token_type": "Bearer",
        "expires_in": 36000,
        "refresh_token": "<your_refresh_token>",
        "scope": "read write groups"
    }

Grab your access_token and start using your new OAuth2 API:

::

    # Retrieve users
    curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/users/
    curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/users/1/

    # Retrieve groups
    curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/groups/

    # Insert a new user
    curl -H "Authorization: Bearer <your_access_token>" -X POST -d"username=foo&password=bar" http://localhost:8000/users/

Step 5: Testing Restricted Access
---------------------------------

Let's try to access resources usign a token with a restricted scope adding a `scope` parameter to the token request

::

    curl -X POST -d "grant_type=password&username=<user_name>&password=<password>&scope=read" http://<client_id>:<client_secret>@localhost:8000/o/token/

As you can see the only scope provided is `read`:

.. code-block:: javascript

    {
        "access_token": "<your_access_token>",
        "token_type": "Bearer",
        "expires_in": 36000,
        "refresh_token": "<your_refresh_token>",
        "scope": "read"
    }

We now try to access our resources:

::

    # Retrieve users
    curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/users/
    curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/users/1/

Ok, this one works since users read only requires `read` scope.

::

    # 'groups' scope needed
    curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/groups/

    # 'write' scope needed
    curl -H "Authorization: Bearer <your_access_token>" -X POST -d"username=foo&password=bar" http://localhost:8000/users/

You'll get a `"You do not have permission to perform this action"` error because your access_token does not provide the
required scopes `groups` and `write`.
