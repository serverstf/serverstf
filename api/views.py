
from django.http import HttpResponse
from django.template import Context, loader
from django.db.models import F

import json
import time
from browser.models import Server, Network, ActivityLog
from api.settings import API_UPDATE_TIMEOUT
import steam.servers

def server_status(request, ids, tail_id):
	
	ids = [int(id) for id in ids.split(",")]
	response = []
	for server in Server.objects.filter(id__in=ids):
		server.update(timeout=API_UPDATE_TIMEOUT)
		
		response.append({
				"id": server.id,
				"name": server.name,
				"host": server.host,
				"port": server.port,
				"map": server.map,
				"player_count": server.player_count,
				"bot_count": server.bot_count,
				"max_players": server.max_players,
				"vac_enabled": server.vac_enabled,
				"password_protected": server.password_protected,
				"network": server.network.id if server.network else None,
				"online": server.is_online,
				#"last_update": time.mktime(server.last_update.timetuple()),
				"location": {
					"latitude": server.latitude,
					"longitude": server.longitude,
					"continent": server.continent_code,
					"country": server.country_code,
					},
				"alltalk": server.alltalk_enabled,
				"teamtalk": server.teamtalk_enabled,
				"crits": server.has_random_crits,
				"bullet_spread": server.has_bullet_spread,
				"damage_spread": server.has_damage_spread,
				"medieval_mode": server.medieval_mode,
				"mods": ["_".join(field.split("_")[1:]) for field 
									in Server._meta.get_all_field_names() 
										if field.startswith("mod_") 
										and getattr(server, field)],
				"favourited": False,
				})
				
		if request.user.is_authenticated():
			if server in request.user.favourites.all():
				response[-1]["favourited"] = True
	
	return HttpResponse(json.dumps(response),
							content_type="application/json")

def server_favourite(request, id):
	
	if request.user.is_authenticated():
		request.user.favourites.add(int(id))
	
	return HttpResponse("")
	
def server_unfavourite(request, id):
	
	if request.user.is_authenticated():
		request.user.favourites.remove(int(id))
		
	return HttpResponse("")

def network_status(request, id):
	
	try:
		network = Network.objects.get(id=id)
	except Network.DoesNotExist:
		return HttpResponse(status=400)
	
	servers = Server.objects.filter(network=network)
	
	context = Context({"network": network, "servers": servers})
	template = loader.get_template("api/network_status.json")
	
	return HttpResponse(template.render(context))

def players_status(request, id):
	
	try:
		server = Server.objects.get(id=id)
	except Server.DoesNotExist:
		return HttpResponse(status=400)
		
	players = steam.servers.ServerQuerier((server.host, server.port)).get_players()
	
	return HttpResponse(json.dumps([player.values for player in players["players"]]))

def activity_status(request, id):
	
	try:
		server = Server.objects.get(id=id)
		als = ActivityLog.objects.filter(server=server).order_by("timestamp")
	except (Server.DoesNotExist, ActivityLog.DoesNotExist):
		return HttpResponse(status=400)
		
		
	s = " ".join(str(al.player_count) for al in als)
	
	return HttpResponse(json.dumps([{
										"player_count": al.player_count,
										"bot_count": al.bot_count,
										"time": time.mktime(al.timestamp.timetuple())
									} for al in als]))


def list_servers(request, region, tags):
	
	tag_handlers = {
					"trade": ("map__startswith", "trade_"),
					"mge": ("map__startswith", "mge_"),
					"jump": ("map__startswith", "jump_"),
					"surf": ("map__startswith", "surf_"),
					"vsh": ("map__startswith", "vsh_"),
					"vac": ("vac_enabled", True),
					"lowgrav": ("lowgrav", True),
					"alltalk": ("alltalk_enabled", True),
					"teamtalk": ("teamtalk_enabled", True),
					"active": ("player_count__gte", F("max_players") * 0.6),
					"full": ("player_count__gte", F("max_players")),
					"bots": ("bot_count__gt", 0),
					"nocrit": ("has_random_crits", False),
					"nobulletspread": ("has_bullet_spread", False),
					"nospread": ("has_damage_spread", False),
					"medieval": ("medieval_mode", True),
					"password": ("password_protected", True),
					
					"smac": ("mod_smac", True),
					"goomba": ("mod_goomba", True),
					"robot": ("mod_robot", True),
					"randomiser": ("mod_randomiser", True),
					"quakesounds": ("mod_quakesounds", True),
					"prophunt": ("mod_prophunt", True),
					"hunted": ("mod_hunted", True),
					"rtd": ("mod_rtd", True),
					"dodgeball": ("mod_dodgeball", True),
					"stats": ("mod_hlxce", True),
					"soap": ("mod_soap", True),
					}
	
	region = region.upper()
	tags = tags.lower()
	
	filters = []
	excludes = []
	for tag in tags.split(","):
		
		if len(tag) < 2:
			continue
		
		try:
			if tag[0] == "-":
				excludes.append(tag_handlers[tag[1:]])
				
			elif tag[0] == "+":
				filters.append(tag_handlers[tag[1:]])
				
			elif tag[0] in ["<", ">"]:
				
				try:
					count = int(tag[1:])
				except ValueError:
					continue
				
				filters.append(({
								"<": "player_count__lt",
								">": "player_count__gt",
								}[tag[0]], count))
		except KeyError:
			pass
		
	svs = Server.objects.filter(continent_code=region, is_online=True)
	for exclude in excludes:
		svs = svs.exclude(**dict([exclude]))
		
	for filter_ in filters:
		svs = svs.filter(**dict([filter_]))
	
	return HttpResponse(json.dumps([sv.id for sv in svs]),
							content_type="application/json")
