Part 1 - Make a Provider in a Minute
====================================

Scenario
--------
You want to make your own :term:`Authorization Server` to issue access tokens to client applications for a certain API.

Start Your App
--------------
During this tutorial you will make an XHR POST from a Heroku deployed app to your localhost instance.
Since the domain that will originate the request (the app on Heroku) is different from the destination domain (your local instance),
you will need to install the `django-cors-middleware <https://github.com/zestedesavoir/django-cors-middleware>`_ app.
These "cross-domain" requests are by default forbidden by web browsers unless you use `CORS <http://en.wikipedia.org/wiki/Cross-origin_resource_sharing>`_.

Create a virtualenv and install `django-oauth-toolkit` and `django-cors-middleware`:

::

    pip install django-oauth-toolkit django-cors-middleware

Start a Django project, add `oauth2_provider` and `corsheaders` to the installed apps, and enable admin:

.. code-block:: python

    INSTALLED_APPS = {
        'django.contrib.admin',
        # ...
        'oauth2_provider',
        'corsheaders',
    }

Include the Django OAuth Toolkit urls in your `urls.py`, choosing the urlspace you prefer. For example:

.. code-block:: python

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),
        url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
        # ...
    ]

Include the CORS middleware in your `settings.py`:

.. code-block:: python

    MIDDLEWARE_CLASSES = (
        # ...
        'corsheaders.middleware.CorsMiddleware',
        # ...
    )

Allow CORS requests from all domains (just for the scope of this tutorial):

.. code-block:: python

    CORS_ORIGIN_ALLOW_ALL = True

.. _loginTemplate:

Include the required hidden input in your login template, `registration/login.html`.
The ``{{ next }}`` template context variable will be populated with the correct
redirect value. See the `Django documentation <https://docs.djangoproject.com/en/dev/topics/auth/default/#django.contrib.auth.views.login>`_
for details on using login templates.

.. code-block:: html

    <input type="hidden" name="next" value="{{ next }}" />

As a final step, execute the migrate command, start the internal server, and login with your credentials.

Create an OAuth2 Client Application
-----------------------------------
Before your :term:`Application` can use the :term:`Authorization Server` for user login,
you must first register the app (also known as the :term:`Client`.) Once registered, your app will be granted access to
the API, subject to approval by its users.

Let's register your application.

Point your browser to http://localhost:8000/o/applications/ and add an Application instance.
`Client id` and `Client Secret` are automatically generated; you have to provide the rest of the informations:

 * `User`: the owner of the Application (e.g. a developer, or the currently logged in user.)

 * `Redirect uris`: Applications must register at least one redirection endpoint before using the
   authorization endpoint. The :term:`Authorization Server` will deliver the access token to the client only if the client
   specifies one of the verified redirection uris. For this tutorial, paste verbatim the value
   `http://django-oauth-toolkit.herokuapp.com/consumer/exchange/`

 * `Client type`: this value affects the security level at which some communications between the client application and
   the authorization server are performed. For this tutorial choose *Confidential*.

 * `Authorization grant type`: choose *Authorization code*

 * `Name`: this is the name of the client application on the server, and will be displayed on the authorization request
   page, where users can allow/deny access to their data.

Take note of the `Client id` and the `Client Secret` then logout (this is needed only for testing the authorization
process we'll explain shortly)

Test Your Authorization Server
------------------------------
Your authorization server is ready and can begin issuing access tokens. To test the process you need an OAuth2
consumer; if you are familiar enough with OAuth2, you can use curl, requests, or anything that speaks http. For the rest
of us, there is a `consumer service <http://django-oauth-toolkit.herokuapp.com/consumer/>`_ deployed on Heroku to test
your provider.

Build an Authorization Link for Your Users
++++++++++++++++++++++++++++++++++++++++++
Authorizing an application to access OAuth2 protected data in an :term:`Authorization Code` flow is always initiated
by the user. Your application can prompt users to click a special link to start the process. Go to the
`Consumer <http://django-oauth-toolkit.herokuapp.com/consumer/>`_ page and complete the form by filling in your
application's details obtained from the steps in this tutorial. Submit the form, and you'll receive a link your users can
use to access the authorization page.

Authorize the Application
+++++++++++++++++++++++++
When a user clicks the link, she is redirected to your (possibly local) :term:`Authorization Server`.
If you're not logged in, you will be prompted for username and password. This is because the authorization
page is login protected by django-oauth-toolkit. Login, then you should see the (not so cute) form a user can use to give
her authorization to the client application. Flag the *Allow* checkbox and click *Authorize*, you will be redirected
again to the consumer service.

__ loginTemplate_

If you are not redirected to the correct page after logging in successfully,
you probably need to `setup your login template correctly`__.

Exchange the token
++++++++++++++++++
At this point your authorization server redirected the user to a special page on the consumer passing in an
:term:`Authorization Code`, a special token the consumer will use to obtain the final access token.
This operation is usually done automatically by the client application during the request/response cycle, but we cannot
make a POST request from Heroku to your localhost, so we proceed manually with this step. Fill the form with the
missing data and click *Submit*.
If everything is ok, you will be routed to another page showing your access token, the token type, its lifetime and
the :term:`Refresh Token`.

Refresh the token
+++++++++++++++++
The page showing the access token retrieved from the :term:`Authorization Server` also let you make a POST request to
the server itself to swap the refresh token for another, brand new access token.
Just fill in the missing form fields and click the Refresh button: if everything goes smoothly you will see the access and
refresh token change their values, otherwise you will likely see an error message.
When you have finished playing with your authorization server, take note of both the access and refresh tokens, we will use them
for the next part of the tutorial.

So let's make an API and protect it with your OAuth2 tokens in the :doc:`part 2 of the tutorial <tutorial_02>`.

