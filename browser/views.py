
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from browser.models import Server, Network
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

def browse_network(request, network_slug):
	return HttpResponse("nope")

@login_required
def browse_favourites(request):
	
	ids = [sv.id for sv in request.user.favourites.all()];

	template = loader.get_template("browser/favourites.html")
	context = RequestContext(request, {
							"tags": [],
							"initial_ids": ids,
							})
	
	return HttpResponse(template.render(context))
	
	
## REST interfaces
from django.http import Http404
from rest_framework import response
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import link
from browser.serialisers import ServerSerialiser
import steam.servers

class ServerViewSet(viewsets.ViewSet):
	
	def retrieve(self, request, pk):
		
		try:
			sv = Server.objects.get(pk=pk)
		except Server.DoesNotExist:
			raise Http404
		
		return response.Response(ServerSerialiser(sv).data)
	
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
			players = []
			for player in sq.get_players()["players"]:
				players.append({
								"name": player["name"],
								"score": player["score"],
								"duration": player["duration"],
								})

			return response.Response(players)
			
		except steam.servers.NoResponseError:
			return response.Response(status=status.HTTP_504_GATEWAY_TIMEOUT)
			
		except steam.servers.BadResponseError:
			return response.Response(statis=HTTP_502_BAD_GATEWAY)
		
