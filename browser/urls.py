
from django.conf.urls import patterns, url

from browser import views

urlpatterns = patterns("",
	url(r"^(?P<region>eu|na|sa|oc|as|af)/(?P<tags>.*)$", views.browse_region, name="browse.region"),
	url(r"^network/(?P<network_slug>[a-zA-Z0-9\-_]+)/?", views.browse_network, name="browse.network"),
	url(r"^favourites$", views.browse_favourites, name="browse.favourites")
)
