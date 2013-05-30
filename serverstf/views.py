
import operator

from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from browser.models import Server, Network
from serverstf import iso3166
from serverstf.forms import SettingsForm

def home(request):
	
	region_pops = {}
	region_cap_usage = {}
	for cont_code in iso3166.CONTINENTS:
		
		svs = Server.objects.filter(continent_code=cont_code)
		
		region_name = iso3166.CONTINENTS[cont_code].title()
		region_pop = sum(sv.player_count for sv in svs)
		region_capacity = sum(sv.max_players for sv in svs)
			
		region_pops[region_name] = region_pop
		region_cap_usage[region_name] = (region_capacity, region_pop)
	
	count_servers = {}
	for count_code in iso3166.ISO3166:
		
		svs = Server.objects.filter(country_code=count_code, is_online=True)
		count_servers[count_code] = svs.count()
		
	map_pops = {}
	for sv in Server.objects.filter(is_online=True):
		
		if sv.map not in map_pops:
			map_pops[sv.map] = 0
		
		map_pops[sv.map] += sv.player_count
	
	mod_servers = {
		"MGE": Server.objects.filter(is_online=True, map__startswith="mge_"),
		"Balloon Race": Server.objects.filter(is_online=True, map__startswith="balloon_"),
		"Surf": Server.objects.filter(is_online=True, map__startswith="surf_"),
		"Jump": Server.objects.filter(is_online=True, map__startswith="jump_"),
		"Prophunt": Server.objects.filter(is_online=True, mod_prophunt=True),
		"SOAP": Server.objects.filter(is_online=True, mod_soap=True),
		}
	mod_servers_pop = {}
	for mod, svs in mod_servers.iteritems():
		mod_servers_pop[mod] = sum(sv.player_count for sv in svs)
	
	template = loader.get_template("home.html")
	context = RequestContext(request, {
							"region_pops": region_pops,
							"count_servers": count_servers,
							"region_cap_usage": region_cap_usage,
							"server_count": Server.objects.all().count(),
							"map_pops": sorted(map_pops.iteritems(), key=operator.itemgetter(1), reverse=True)[:7],
							"mod_servers": mod_servers_pop,
							})
	
	return HttpResponse(template.render(context))

@login_required
def manage_settings(request):
	
	#if request.method == "POST":
		#form = SettingsForm(request.POST)
		
	form =  SettingsForm()
	
	template = loader.get_template("settings.html")
	context = RequestContext(request, {
							"form": form,
							})
	
	return HttpResponse(template.render(context))
