
import logging
log = logging.getLogger(__name__)

import datetime
import random

from django.db import models
import steam.servers
import socket

import browser.settings

import pygeoip
try:
	geoip = pygeoip.GeoIP(browser.settings.GEOIP_CITY_DATA)
except IOError:
	geoip = None

class Network(models.Model):
	
	name = models.CharField(max_length=128)
	slug = models.SlugField(max_length=24)
	url = models.URLField(blank=True)
	
	def __unicode__(self):
		return self.name

class Server(models.Model):
	
	PURE_NONE = 0
	PURE_WARN = 1
	PURE_KICK = 2
	
	MODE_ARENA = 0
	MODE_CP = 1
	MODE_CTF = 2
	MODE_MVM = 3
	MODE_PAYLOAD = 4
	MODE_SD = 5
	
	## Core details
	network = models.ForeignKey(Network, null=True, blank=True)
	name = models.CharField(max_length=128)
	host = models.CharField(max_length=128)
	port = models.PositiveIntegerField()
	map = models.CharField(max_length=64, editable=False)
	player_count = models.PositiveIntegerField(default=0, editable=False)
	bot_count = models.PositiveIntegerField(default=0, editable=False)
	max_players = models.PositiveIntegerField(default=0, editable=False)
	vac_enabled = models.BooleanField(default=False, editable=False)
	password_protected = models.BooleanField(default=False, editable=False)
	is_online = models.BooleanField(default=False, editable=False)
	description = models.TextField(max_length=512, default="", blank=True)
	
	## Updates
	last_update = models.DateTimeField(auto_now_add=True) # TODO: rename last_update_info
	last_update_rules = models.DateTimeField(auto_now_add=True)
	last_update_online = models.DateTimeField(auto_now_add=True) # TODO: rename last_update
	
	## Voice chat
	alltalk_enabled = models.BooleanField(default=False, editable=False)
	teamtalk_enabled = models.BooleanField(default=False, editable=False)
	
	## Purity
	# sv_pure_kick_clients
	# purity = models.IntegerField(default=0, editable=False,
	#									choices=(PURE_WARN, PURE_KICK))
	
	## Holiday modes
	# birthday_mode = models.BooleanField(default=False, editable=False)
	# halloween_mode = models.BooleanField(default=False, editable=False)
	# etc, tfh_*
	
	## Compesque settings
	has_damage_spread = models.BooleanField(default=True, editable=False) # tf_damage_disablespread
	has_bullet_spread = models.BooleanField(default=True, editable=False) # tf_use_fixed_weaponspreads
	has_random_crits = models.BooleanField(default=True, editable=False) # tf_weapon_criticals
	# tournament_mode = models.BooleanField(default=False, editable=False) # mp_tournament
	
	## Mods
	mod_rtd = models.BooleanField(default=False, editable=False)
	mod_randomiser = models.BooleanField(default=False, editable=False)
	mod_quakesounds = models.BooleanField(default=False, editable=False)
	mod_prophunt = models.BooleanField(default=False, editable=False)
	mod_robot = models.BooleanField(default=False, editable=False)
	mod_hunted = models.BooleanField(default=False, editable=False)
	mod_medipacks = models.BooleanField(default=False, editable=False)
	mod_dodgeball = models.BooleanField(default=False, editable=False)
	mod_mge = models.BooleanField(default=False, editable=False)
	mod_goomba = models.BooleanField(default=False, editable=False)
	mod_smac = models.BooleanField(default=False, editable=False)
	mod_hlxce = models.BooleanField(default=False, editable=False)
	mod_soap = models.BooleanField(default=False, editable=False)
	
	## Misc
	lowgrav = models.BooleanField(default=False, editable=False) # sv_gravity < 800
	allows_cheats = models.BooleanField(default=False, editable=False)
	medieval_mode = models.BooleanField(default=False, editable=False) # tf_medieval
	
	# From GeoIP
	longitude = models.FloatField(editable=False, null=True)
	latitude = models.FloatField(editable=False, null=True)
	country_code = models.CharField(editable=False, null=True, max_length=2)
	continent_code = models.CharField(editable=False, null=True, max_length=2)
	
	def __unicode__(self):
		return self.name
	
	def update(self, force=False, timeout=5.0):
		
		mod_cvar_map = {
			"mod_rtd": ["sm_rtd_version"],
			"mod_randomiser": ["tf2items_rnd_version"],
			"mod_quakesounds": ["sm_quakesounds_version"],
			"mod_prophunt": ["sm_prophunt_version"],
			"mod_robot": ["sm_betherobot_version"],
			"mod_hunted": ["sm_hunted_version"],
			"mod_medipacks": ["sm_medipacks_version"],
			"mod_dodgeball": ["tf_dodgeball_version", "sm_dodgeball_version"],
			"mod_mge": ["sm_mgemod_version"],
			"mod_goomba": ["goomba_version"],
			"mod_smac": ["smac_version"],
			"mod_hlxce": ["hlxce_version"],
			"mod_soap": [
						"soap_kill_ammo",
						"soap_kill_heal_ratio",
						"soap_kill_heal_static",
						"soap_opendoors",
						"soap_regen_delay",
						"soap_regenhp",
						"soap_regentick",
						"soap_showhp",
						"soap_spawn_delay",
						"soap_spawnrandom",
						]
			}
		
		update_info = datetime.datetime.now() >= self.last_update + browser.settings.SERVER_UPDATE_TD_INFO or force
		update_rules = datetime.datetime.now() >= self.last_update_rules + browser.settings.SERVER_UPDATE_TD_RULES or force
		update_online = datetime.datetime.now() >= self.last_update_online + browser.settings.SERVER_UPDATE_TD_ONLINE or force
		
		self.last_update_online = datetime.datetime.now()
		if not self.is_online and not update_online and not force:
			return
		
		try:
			sq = steam.servers.ServerQuerier((self.host, self.port), timeout)
			
			if update_info:

				sqi = sq.get_info()
				self.is_online = True
				
				self.name = sqi["server_name"]
				self.player_count = sqi["player_count"] - sqi["bot_count"]
				self.max_players = sqi["max_players"]
				self.bot_count = sqi["bot_count"]
				self.map = sqi["map"]
				self.password_protected = sqi["password_protected"]
				self.vac_enabled = sqi["vac_enabled"]
				
				self.last_update = datetime.datetime.now()
				self.last_update_online = datetime.datetime.now()
				
			# Some servers appear to report really odd values for 
			# tf_weapon_criticals, e.g. 500, 80.0 and 1000. Will interpret
			# any non-zero value to be True.
			
			# Because of this other cvars may be reported incorrectly.
			# BE AWARE, BE AFRAID
			
			# Yep, some servers also have complete jibberish for others.
			
			if update_rules:
				sqr = sq.get_rules()["rules"]
				self.is_online = True

				try:
					self.has_damage_spread = not bool(int(sqr.get("tf_damage_disablespread", 0)))
					self.has_bullet_spread = not bool(int(sqr.get("tf_use_fixed_weaponspreads", 0)))
					self.has_random_crits = bool(float(sqr.get("tf_weapon_criticals", 1)))
					
					self.lowgrav = float(sqr.get("sv_gravity", 800)) < 800
					self.allows_cheats = bool(int(sqr.get("sv_cheats", 0)))
					self.alltalk_enabled = bool(int(sqr.get("sv_alltalk", 0)))
					self.teamtalk_enabled = bool(int(sqr.get("tf_teamtalk", 0)))
					self.medieval_mode = bool(int(sqr.get("tf_medieval", 0)))
				except ValueError:
					pass
					
				for field, cvars in mod_cvar_map.iteritems():
					setattr(self, field, False)
					for cvar in cvars:
						if cvar in sqr:
							setattr(self, field, True)
				
				self.last_update_rules = datetime.datetime.now()
				self.last_update_online = datetime.datetime.now()
				
		except steam.servers.NoResponseError:
			self.is_online = False
		except steam.servers.BrokenMessageError:
			pass
		except socket.error as exc:
			log.exception("Unexpected socket error for {}:{}".format(self.host, self.port))
		except NotImplementedError as exc:
			log.error("Compressed response from {}:{}".format(self.host, self.port))
		
		self.save()
	
	def update_geoip(self):
		
		global geoip
		
		if geoip is None:
			geoip = pygeoip.GeoIP(browser.settings.GEOIP_CITY_DATA)
			
		geoip_record = geoip.record_by_addr(socket.gethostbyname(self.host))
		try:
			self.country_code = geoip_record["country_code"].upper()
			self.continent_code = geoip_record["continent"].upper()
			self.longitude = float(geoip_record["longitude"])
			self.latitude = float(geoip_record["latitude"])
		except KeyError:
			# No reliable location data so null everything
			self.country_code = None
			self.continent_code = None
			self.longitude = None
			self.latitude = None
			
		self.save()
	
class ActivityLog(models.Model):
	
	server = models.ForeignKey(Server)
	timestamp = models.DateTimeField(auto_now_add=True)
	player_count = models.IntegerField()
	bot_count = models.IntegerField()
	
	@classmethod
	def from_server(cls, server):
		
		server.update()
		
		return cls(
					server=server,
					player_count=server.player_count,
					bot_count=server.bot_count
					)
