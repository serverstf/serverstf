
from rest_framework import serializers
from steam_auth.models import User

class UserSerialiser(serializers.ModelSerializer):
	
	class Meta:
		model = User
		fields = ["id", "profile_name", "avatar", "is_admin",
			"steam_id", "favourites"]
