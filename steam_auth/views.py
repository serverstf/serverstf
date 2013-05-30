
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

from django.contrib import auth
User = auth.get_user_model()

from steam_auth.settings import OPENID_FILESTORE_LOCATION

import openid.consumer.consumer
import openid.store.filestore

import steam.id

oid_store = openid.store.filestore.FileOpenIDStore(OPENID_FILESTORE_LOCATION)

# Example:
# https://github.com/openid/python-openid/tree/master/examples/djopenid

def auth_start(request):
	"""
		Begins the OpenID login procedure by redirecting the user to the
		Steam login page.
	"""
	# TODO: ?continue=/
	oid_cons = openid.consumer.consumer.Consumer(request.session, oid_store)
	auth_request = oid_cons.begin("http://steamcommunity.com/openid")
	
	template = loader.get_template("steam_auth/notice.html")
	context = RequestContext(request, {
					"redirect_url": auth_request.redirectURL("http://localhost:8000/", "http://localhost:8000/openid/handle"),
					})
	
	return HttpResponse(template.render(context))
	
def auth_return(request):
	"""
		Handles the redirect from Steam back to the site. Takes the 
		returned SteamID to either create a new User or log in an
		existing user with that SteamID.
	"""
	
	oid_cons = openid.consumer.consumer.Consumer(request.session, oid_store)
	oid_resp = oid_cons.complete(request.REQUEST, request.build_absolute_uri())
	
	if oid_resp.status == openid.consumer.consumer.SUCCESS:
		# I have the feeling that the oid_resp would expose a way to
		# access the claimed_id/identity without having to directly
		# access the GET parameters, however this'll do for now
		
		# http://steamcommunity.com/openid/id/<steamid>
		# According to http://steamcommunity.com/dev
		try:
			steam_id = steam.id.SteamID.from_community_url(request.GET["openid.claimed_id"])
		except (steam_id.SteamIDError, KeyError):
			return HttpResponse("Bad Steam response or invalid SteamID returned")
			
		try:
			user = User.objects.get(steam_id=steam_id)
			#return HttpResponse(str(u.steam_id))
		except User.DoesNotExist:
			user = User.objects.create_user(steam_id=steam_id)
			#return HttpResponse("Created user with SteamID: {}".format(steam_id))
		
		# No custom backends so it's safe to set it manually ... I hope
		user.backend = "django.contrib.auth.backends.ModelBackend"
		auth.login(request, user)
		
		user.syncronise()

		return HttpResponseRedirect(request.GET.get("next", "/"))
		
	elif oid_resp.status == openid.consumer.consumer.FAILURE:
		return HttpResponse("Lame. Authentication totally didn't work.")
	elif oid_resp.status == openid.consumer.consumer.CANCEL:
		return HttpResponse("Aborted! D:")

def logout_(request):
	auth.logout(request)
	return HttpResponseRedirect(request.GET["next"])
