
from rest_framework import serializers
from lobby.models import Party

class PartySerialiser(serializers.ModelSerializer):
	
	class Meta:
		model = Party
		fields = ["id", "map", "type", "config", "members"]
