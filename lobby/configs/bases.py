
import lobby.configs

class Config(object):
	
	def __init__(self, cvars, state=None):
		
		self.cvars = cvars
		self.state = state or {}
		
	def configure(self, rcon):
		"""
			Configures a server via RCON by setting the various cvars.
			An attempt will be made to store the current state of the
			cvar to the 'state' dictionary.
			
			Assumes the RCON instance is authenticated.
		"""
		
		for cvar, value in self.cvars:
			
			if cvar == "exec":
				try:
					cfg = lobby.configs.all_configs[value]()
				except KeyError:
					raise lobby.configs.ConfigurationError("No config '{}'".foramt(value))
				
				cfg.configure(rcon)
				self.state.update(cfg.state)
			else:
				with rcon.response_to(rcon.execute(cvar)) as response:
					self.state[cvar] = response.body
					rcon.execute("{} {}".format(cvar, value))
	
	def revert(self, rcon):
		"""
			Attempts to revert the server to a previous state via RCON.
			
			Assumes the RCON instance is authenticated.
		"""
		# TODO: ALL OF THIS
		for cvar, value in self.state.iteritems():
			rcon.execute("{} {}".format(cvar, value))
	
class TextConfig(Config):
	"""
		Config class for new-line sperated config scripts. Will not
		work correctly if multiple commands are on one line, e.g.
		semicolon seperated.
	"""
	
	# script = ...
	
	def __init__(self, script=None):
		
		if script is None:
			script = self.__class__.script
		
		cvars = []
		for line in script.split("\n"):
			split = line.lstrip().split()
			if len(split) < 1:
				continue
			
			cvars.append((split[0], " ".join(split[1:])))
		
		Config.__init__(self, cvars)
