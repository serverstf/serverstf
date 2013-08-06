
from django.conf import settings
from django.db import models

from browser.models import Server
import lobby.configs

class Lobby(models.Model):
	
	SIXES = 1
	HIGHLANDER = 2
	ULTIDUO = 3
	
	TYPE_CHOICES = (
		(SIXES, "6v6"),
		(HIGHLANDER, "Highlander"),
		(ULTIDUO, "Ultiduo"),
		)
	
	CREATED = 0
	CONFIGURED = 1
	STARTED = 2
	IN_PROGRESS = 3
	FINISHED = 4
	COMPLETE = 5
	
	# ---- Lobby States ----
	#
	# CREATED
	# Default state of freshly created lobbies. Server will be
	# configured with hte specified config.
	#
	# CONFIGURED
	# The lobby manager has finished configuring the server and the
	# lobby is now accepting players.
	#
	# STARTED
	# The lobby had all slots filled and is about to begin. All players
	# should be connecting to the server. A timeout can be applied, so
	# that if not all players onnect ina given time, the state can either
	# be reverted back to CONFIGURED (to fill missing slot) or In_PROGRESS 
	# (to start anyway.)
	#
	# IN_PROGRESS
	# The game is underway. Stats will be being reported to a statistics
	# colelctor daemon. The server will be polled to test if the win
	# condition has been met and the state can be advanced.
	#
	# FINISHED
	# A win condition was met and all players will be booted from the
	# server if they haven't already vaccated it. An attempt will be
	# made to revert server to pre-configuration state.
	#
	# COMPLETE
	# The lobby is over. 'rcon_password' should be wiped.
	
	STATE_CHOICES = (
		(CREATED, "Created"),
		(CONFIGURED, "Configured"),
		(STARTED, "Started"),
		(IN_PROGRESS, "In progress"),
		(FINISHED, "Finished"),
		(COMPLETE, "Complete")
		)
	
	# ETF2L configs
	ETF2L_6V6_5CP = lobby.configs.etf2l.Sixes5CP.id
	ETF2L_6V6_KOTH = lobby.configs.etf2l.SixesKOTH.id
	ETF2L_6V6_CTF = lobby.configs.etf2l.SixesCTF.id
	ETF2L_6V6_STOPWATCH = lobby.configs.etf2l.SixesStopwatch.id
	
	ETF2L_HL_5CP = lobby.configs.etf2l.Highlander5CP.id
	ETF2L_HL_KOTH = lobby.configs.etf2l.HighlanderKOTH.id
	ETF2L_HL_CTF = lobby.configs.etf2l.HighlanderCTF.id
	ETF2L_HL_STOPWATCH = lobby.configs.etf2l.HighlanderStopwatch.id
	
	ETF2L_ULTIDUO = lobby.configs.etf2l.Ultiduo.id
#	
#	# UGC configs
#	UGC_6V6_5CP = lobby.configs.ugc.Highlander5CP.id
#	UGC_6V6_KOTH = lobby.configs.ugc.HighlanderKOTH.id
#	UGC_6V6_CTF = lobby.configs.ugc.HighlanderKOTH.id
#	UGC_6V6_STOPWATCH = lobby.configs.ugc.HighlanderStopwatch.id
#	
#	UGC_HL_5CP = lobby.configs.ugc.Highlander5CP.id
#	UGC_HL_KOTH = lobby.configs.ugc.HighlanderKOTH.id
#	UGC_HL_CTF = lobby.configs.ugc.HighlanderKOTH.id
#	UGC_HL_STOPWATCH = lobby.configs.ugc.HighlanderStopwatch.id
#	UGC_HL_TOW = lobby.configs.ugc.HighlanderTugOfWar.id
	
	CONFIG_CHOICES = (
		(ETF2L_6V6_5CP, "ETF2L 6v6 5CP"),
		(ETF2L_6V6_KOTH, "ETF2L 6v6 KOTH"),
		(ETF2L_6V6_CTF, "ETF2L 6v6 CTF"),
		(ETF2L_6V6_STOPWATCH, "ETF2L 6v6 Stopwatch"),
		(ETF2L_HL_5CP, "ETF2L Highlander 5CP"), 
		(ETF2L_HL_KOTH, "ETF2L Highlander KOTH"),
		(ETF2L_HL_CTF, "ETF2L Highlander CTF"),
		(ETF2L_HL_STOPWATCH, "ETF2L Highlander Stopwatch"),
		(ETF2L_ULTIDUO, "ETF2L Ultiduo"),
#		
#		(UGC_6V6_5CP, "UGC 6v6 5CP"),
#		(UGC_6V6_KOTH, "UGC 6v6 KOTH"),
#		(UGC_6V6_CTF, "UGC 6v6 CTF"),
#		(UGC_6V6_STOPWATCH, "UGC 6v6 Stopwatch"),
#		(UGC_HL_5CP, "UGC Highlander 5CP"), 
#		(UGC_HL_KOTH, "UGC Highlander KOTH"),
#		(UGC_HL_CTF, "UGC Highlander CTF"),
#		(UGC_HL_STOPWATCH, "UGC Highlander Stopwatch"),
		)
	
	ALLOWED_CONFIGS = {
		SIXES: {
			ETF2L_6V6_5CP,
			ETF2L_6V6_KOTH,
			ETF2L_6V6_CTF,
			ETF2L_6V6_STOPWATCH,
			#UGC_6V6_5CP,
			#UGC_6V6_KOTH,
			#UGC_6V6_CTF,
			#UGC_6V6_STOPWATCH,
			},
		HIGHLANDER: {
			ETF2L_HL_5CP,
			ETF2L_HL_KOTH,
			ETF2L_HL_CTF,
			ETF2L_HL_STOPWATCH,
			#UGC_HL_5CP,
			#UGC_HL_KOTH,
			#UGC_HL_CTF,
			#UGC_HL_STOPWATCH,
			},
		ULTIDUO: {
			ETF2L_ULTIDUO,
			},
		}
	
	type = models.SmallIntegerField(choices=TYPE_CHOICES)
	state = models.SmallIntegerField(
					choices=STATE_CHOICES,
					editable=False,
					default=CREATED)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL)
	created = models.DateTimeField(auto_now_add=True)
	
	# Couldn't find reference to max length of RCON passwords; 128
	# should be more than enough
	
	# CLEAR THIS ONCE A LOBBY IS COMPLETE
	rcon_password = models.CharField(max_length=128)
	
	server = models.ForeignKey(Server)
	map = models.CharField(max_length=64)
	config = models.CharField(max_length=32, choices=CONFIG_CHOICES)

	def __unicode__(self):
		return u"{}'s {} lobby on {}".format(
			self.owner.get_short_name(),
			self.config,
			self.map
			)
	
