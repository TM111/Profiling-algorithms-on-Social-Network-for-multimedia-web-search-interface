from django.conf.urls import url
from app import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.results_list, name='results_list'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'},name='logout'),
    url(r'^signup/$', views.signup, name='signup'),
]
