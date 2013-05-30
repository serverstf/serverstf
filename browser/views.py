
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from browser.models import Server, Network
from serverstf import iso3166

import json

def browse_all(request):
	
	template = loader.get_template("browser/browse_all.html")
	context = RequestContext(request, {"servers": Server.objects.all()})
	
	return HttpResponse(template.render(context))

def browse_region(request, region, tags):
	
	region = region.upper()
	tags = [tag for tag in tags.split(",") if tag]
	
	template = loader.get_template("browser/browse_all.html")
	context = RequestContext(request, {
							"tags": tags,
							
							"title": iso3166.CONTINENTS.get(region, ""),
							
							"region": region,
							"batch_size": 10,
							"allow_relist": True,
							"initial_ids": "[]"
							})
	
	return HttpResponse(template.render(context))

def browse_network(request, network_slug):
	return HttpResponse("nope")

@login_required
def browse_favourites(request):
	
	ids = [sv.id for sv in request.user.favourites.all()];
	
	template = loader.get_template("browser/browse_all.html")
	context = RequestContext(request, {
							"tags": [],
							
							"title": "Favourites",
							
							"region": "~",
							"batch_size": 10,
							"allow_relist": False,
							"initial_ids": json.dumps(ids),
							})
	
	return HttpResponse(template.render(context))
