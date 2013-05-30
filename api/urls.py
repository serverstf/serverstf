
from django.conf.urls import patterns, url

from api import views

urlpatterns = patterns("",
	url(r"^server/(\d+(,\d+)*)$", views.server_status, name="api.server"),
	url(r"^server/(?P<id>\d+)/favourite$", views.server_favourite, name="api.server.favourite"),
	url(r"^server/(?P<id>\d+)/unfavourite$", views.server_unfavourite, name="api.server.unfavourite"),
	url(r"^server/(?P<id>\d+)/players/?$", views.players_status, name="api.server.players"),
	url(r"^server/(?P<id>\d+)/activity/?$", views.activity_status, name="api.server.activity"),
	url(r"^network/(?P<id>\d+)/?$", views.network_status, name="api.network"),
	url(r"^list/(?P<region>eu|na|sa|af|as|oc)/(?P<tags>.*)$", views.list_servers, name="api.list"),
)
