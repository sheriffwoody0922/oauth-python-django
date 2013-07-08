from __future__ import absolute_import
from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^authorize/$', views.AuthorizationView.as_view(), name="authorize"),
    url(r'^token/$', views.TokenView.as_view(), name="token"),
)

# Application management views
urlpatterns += patterns(
    '',
    url(r'^applications/$', views.ApplicationList.as_view(), name="applications_list"),
    url(r'^applications/register/$', views.RegistrationView.as_view(), name="applications_register"),
    url(r'^applications/(?P<pk>\d+)$', views.ApplicationDetail.as_view(), name="applications_detail"),
)
