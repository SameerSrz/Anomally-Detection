from . import views
from django.urls import path
from django.conf.urls import url
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    path('images/', views.post_alert, name='post_alert'),
    url(r'^get_auth_token/$', rest_framework_views.obtain_auth_token, name='get_auth_token'),
]