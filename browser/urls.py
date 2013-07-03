
from django.conf.urls import patterns, url

from browser import views

urlpatterns = patterns("",
	url(r"^(?P<region>eu|na|sa|oc|as|af|all|~)/?$", views.browse_region, name="browse.region"),
	url(r"^favourites$", views.browse_favourites, name="browse.favourites"),
	
	url(r"^network/(?P<slug>[a-zA-Z0-9\-_]+)/manage", views.manage_network, name="manage.network"),
	url(r"^network/(?P<slug>[a-zA-Z0-9\-_]+)/?", views.browse_network, name="browse.network"),
)
