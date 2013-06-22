
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
