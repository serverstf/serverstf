
import datetime

from celery import task
from django.contrib.auth import get_user_model
# Cannot User = get_user_model() due to circular imports

import steam.api
from steam_auth.settings import STEAM_API_KEY
steam_api = steam.api.SteamAPI(STEAM_API_KEY)

@task()
def synchronise_profiles(user_id):
	
	User = get_user_model()
	try:
		user = User.objects.get(id=user_id)
	except User.DoesNotExist:
		return
	
	player_summary = steam_api.user.get_player_summaries(
						steamids=int(user.steam_id))["response"]["players"][0]
	
	user.profile_name = player_summary["personaname"]
	user.avatar = player_summary["avatarmedium"]
	user.last_sync = datetime.datetime.now()
	
	user.save()
