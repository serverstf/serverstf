

from django.conf.urls import patterns, url

from lobby import views

urlpatterns = patterns("",
	url(r"^$", views.main, name="lobby.main"),
	url(r"^create$", views.create, name="lobby.create"),
	url(r"^party/join/(?P<id>\d+)$", views.join_party, name="lobby.party.join"),
)
