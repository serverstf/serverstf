
from rest_framework import serializers

from browser.models import Server

class ServerLocationSerialiser(serializers.Serializer):
	
	longitude = serializers.FloatField()
	latitude = serializers.FloatField()
	country = serializers.CharField(source="country_code", max_length=2)
	continent = serializers.CharField(source="continent_code", max_length=2)

class ServerModsSerialiser(serializers.Serializer):
	
	rtd = serializers.BooleanField(source="mod_rtd")
	randomiser = serializers.BooleanField(source="mod_randomiser")
	quakesounds = serializers.BooleanField(source="mod_quakesounds")
	prophunt = serializers.BooleanField(source="mod_prophunt")
	robot = serializers.BooleanField(source="mod_robot")
	hunted = serializers.BooleanField(source="mod_hunted")
	medipacks = serializers.BooleanField(source="mod_medipacks")
	dodgeball = serializers.BooleanField(source="mod_dodgeball")
	mge = serializers.BooleanField(source="mod_mge")
	goomba = serializers.BooleanField(source="mod_goomba")
	smac = serializers.BooleanField(source="mod_smac")
	hlxce = serializers.BooleanField(source="mod_hlxce")
	soap = serializers.BooleanField(source="mod_soap")

class ServerConfigSerialiser(serializers.Serializer):
	
	alltalk = serializers.BooleanField(source="alltalk_enabled")
	teamtalk = serializers.BooleanField(source="teamtalk_enabled")
	damage_spread = serializers.BooleanField(source="has_damage_spread")
	bullet_spread = serializers.BooleanField(source="has_bullet_spread")
	crits = serializers.BooleanField(source="has_random_crits")
	lowgrav = serializers.BooleanField()
	cheats = serializers.BooleanField(source="allows_cheats")
	medieval = serializers.BooleanField(source="medieval_mode")

class ServerSerialiser(serializers.Serializer):
	
	id = serializers.IntegerField()
	name = serializers.CharField(max_length=128)
	host = serializers.CharField(max_length=128)
	port = serializers.IntegerField()
	map = serializers.CharField(max_length=64)
	player_count = serializers.IntegerField()
	bot_count = serializers.IntegerField()
	max_players = serializers.IntegerField()
	vac_enabled = serializers.BooleanField()
	password_protected = serializers.BooleanField()
	online = serializers.BooleanField(source="is_online")
	favourited = serializers.SerializerMethodField("is_favourited")
	
	config = ServerConfigSerialiser(source="*")
	mods = ServerModsSerialiser(source="*")
	location = ServerLocationSerialiser(source="*")
	
	def is_favourited(self, server):
		return server in self.context["user"].favourites.all()
	
## /players
class PlayersSerialiser(serializers.Serializer):
	
	name = serializers.CharField()
	score = serializers.IntegerField()
	duration = serializers.FloatField()

## /activity
class ActivitySerialiser(serializers.Serializer):
	
	bot_count = serializers.IntegerField()
	player_count = serializers.IntegerField()
	timestamp = serializers.DateTimeField()

# Don't repeat yourself they said
