
from django.http import HttpResponse, Http404
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from browser.models import Server, Network, ActivityLog
from browser.forms import NetworkForm
from serverstf import iso3166

import json

def browse_region(request, region, tags):
	
	region = region.upper()
	tags = [tag for tag in tags.split(",") if tag]
	
	template = loader.get_template("browser/region.html")
	context = RequestContext(request, {
							"tags": tags,
							"region": region,
							})
	
	return HttpResponse(template.render(context))

def browse_network(request, slug):
	
	try:
		network = Network.objects.get(slug=slug)
	except Network.DoesNotExist:
		raise Http404
	
	ids = [sv.id for sv in network.servers.all()]
	
	template = loader.get_template("browser/network.html")
	context = RequestContext(request, {
							"network": network,
							"tags": [],
							"region": "~",
							"initial_ids": ids,
							})
	
	return HttpResponse(template.render(context))

@login_required
def manage_network(request, slug):
	
	try:
		network = Network.objects.get(slug=slug)
	except Network.DoesNotExist:
		raise Http404
	
	if request.user not in network.admins.all():
		return HttpResponse("You're not an admin of this network", status=401)
	
	if request.method == "POST":
		form = NetworkForm(request.POST)
	else:
		form  = NetworkForm(instance=network)
	
	template = loader.get_template("browser/network_manage.html")
	context = RequestContext(request, {
							"network": network,
							"form": form,
							})
	
	return HttpResponse(template.render(context))

@login_required
def browse_favourites(request):
	
	ids = [sv.id for sv in request.user.favourites.all()]

	template = loader.get_template("browser/favourites.html")
	context = RequestContext(request, {
							"tags": [],
							"initial_ids": ids,
							})
	
	return HttpResponse(template.render(context))
	
	
## REST interfaces
from rest_framework import response
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import link, action
from browser.serialisers import ServerSerialiser, \
									ActivitySerialiser, \
									PlayersSerialiser
from browser.settings import API_UPDATE_TIMEOUT
import steam.servers

class ServerViewSet(viewsets.ViewSet):
	
	def retrieve(self, request, pk):
		
		try:
			sv = Server.objects.get(pk=pk)
		except Server.DoesNotExist:
			raise Http404
		
		try:
			update_flag = int(request.QUERY_PARAMS.get("update", 0))
		except ValueError:
			update_flag = 0
		
		if update_flag:
			sv.update(timeout=API_UPDATE_TIMEOUT)
		
		return response.Response(ServerSerialiser(sv,
									context={"user": request.user}).data)
	
	@link()
	def search(self, request, pk):
		return response.Response(
				[sv.id for sv in  Server.objects.search(pk.split(","),
								request.QUERY_PARAMS.get("region", "all"))])
								
	@link()
	def players(self, request, pk):
		
		try:
			sv = Server.objects.get(pk=pk)
		except Server.DoesNotExist:
			raise Http404
			
		sq = steam.servers.ServerQuerier((sv.host, sv.port))
		
		try:
			# This is a hopefully temporary workaround for the fact
			# that it seems impossible to speficy as subsript as a
			# source to a serialiser field, e.g.
			# name = CharField(source="['name']")
			class _DictAttrWrapper(object):
				
				def __init__(self, dict_):
					self.dict = dict_
					
				def __getattr__(self, key):
					
					try:
						return self.dict[key]
					except KeyError as exc:
						raise AttributeError(exc)
			
			players = [_DictAttrWrapper(p) for p in sq.get_players()["players"]]
			return response.Response(PlayersSerialiser(
											players, many=True).data)
			
		except steam.servers.NoResponseError:
			return response.Response(status=status.HTTP_504_GATEWAY_TIMEOUT)
			
		except steam.servers.BrokenMessageError:
			return response.Response(statis=HTTP_502_BAD_GATEWAY)
		
	@link()
	def activity(self, request, pk):
		
		try:
			server = Server.objects.get(pk=pk)
			als = ActivityLog.objects.filter(server=server).order_by("timestamp")
		except (Server.DoesNotExist, ActivityLog.DoesNotExist):
			return Http404

		return response.Response(ActivitySerialiser(als, many=True).data)
	
	# I'm somewhat concered that 'favourite' and 'unfavourite' may not
	# be strictly "RESTful" and that the favourites list should be exposed
	# as it's own 'resource'
	
	@action()
	def favourite(self, request, pk):
		
		try:
			sv = Server.objects.get(pk=pk)
		except Server.DoesNotExist:
			raise Http404
		
		if request.user.is_authenticated():
			request.user.favourites.add(sv)
			return response.Response(status=status.HTTP_204_NO_CONTENT)
		
		return response.Response(status=status.HTTP_401_UNAUTHORIZED)
		
	@action()
	def unfavourite(self, request, pk):
		
		try:
			sv = Server.objects.get(pk=pk)
		except Server.DoesNotExist:
			raise Http404
			
		if request.user.is_authenticated():
			request.user.favourites.remove(sv)
			return response.Response(status=status.HTTP_204_NO_CONTENT)
			
		return response.Response(status=status.HTTP_401_UNAUTHORIZED)
