
from celery import task

from lobby.models import Lobby
import lobby.configs

import steam.rcon

def load_model(f):
	return lambda id: f(Lobby.objects.get(id=id))

@task()
@load_model
def configure(lobbie):
	
	rcon = steam.rcon.RCON(lobbie.server.address)
	rcon.authenticate(lobbie.rcon_password)
	
	cfg = lobby.configs.all_configs[lobbie.config]()
	cfg.configure(rcon)
	
	# TODO: serialise and store state for later reversion

@task()
@load_model
def start(lobbie):
	"""
		Will start the lobby if all slots filled.
		
		Client side will issue connection details to all players.
		Once all players are on the server, state will be progressed
		to IN_PROGRESS.
	"""
	
	pass
