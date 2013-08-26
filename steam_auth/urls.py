
from django.conf.urls import patterns, url

from steam_auth import views

urlpatterns = patterns("",
	url(r"^login$", views.auth_start, name="login"),
	url(r"^logout$", views.logout_, name="logout"),
	url(r"^handle$", views.auth_return),
	url(r"^settings$", views.manage_settings, name="settings.handler"),
)
