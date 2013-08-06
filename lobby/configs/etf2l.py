
from lobby.configs.bases import TextConfig

class BaseConfig(TextConfig):
	
	id = "etf2l_base"
	script = """
	log on

	tv_delay 90
	tv_delaymapchange 1
	tv_transmitall 1

	mp_allowspectators 1
	mp_bonusroundtime 0
	mp_disable_respawn_times 0
	mp_fadetoblack 0
	mp_footsteps 1
	mp_forcecamera 1
	mp_fraglimit 0
	mp_idledealmethod 0
	mp_match_end_at_timelimit 1
	mp_respawnwavetime 10.0
	mp_stalemate_enable 0
	mp_teams_unbalance_limit 0
	mp_tournament 1
	mp_tournament_allow_non_admin_restart 0
	mp_tournament_stopwatch 1

	sv_allow_votes 0
	sv_allow_wait_command 0
	sv_alltalk 0
	sv_cheats 0
	sv_client_max_interp_ratio 5
	sv_client_min_interp_ratio 1
	sv_client_predict 1
	sv_consistency 1
	sv_gravity 800
	sv_maxcmdrate 66
	sv_maxrate 0
	sv_maxupdaterate 66
	sv_mincmdrate 40
	sv_minrate 0
	sv_minupdaterate 40
	sv_pausable 1
	sv_pure 2
	sv_pure_kick_clients 1
	sv_restrict_aspect_ratio_fov 0
	sv_timeout 10

	tf_arena_first_blood 0
	tf_avoidteammates_pushaway 0
	tf_clamp_airducks 1
	tf_ctf_bonus_time 0
	tf_damage_disablespread 1
	tf_flag_caps_per_round 0
	tf_teamtalk 1
	tf_tournament_hide_domination_icons 1
	tf_use_fixed_weaponspreads 1
	tf_weapon_criticals 0

	mp_tournament_restart

	say ETF2L config (2012-09-28) loaded.
	say * Please check that the settings are correct for this game mode!
	say * You must record POV demos and take screenshots of all results.
	"""

class SixesBase(TextConfig):
	
	id = "etf2l_base_6v6"
	script = """
	mp_tournament_whitelist "cfg/etf2l_whitelist_6v6.txt"

	tf_tournament_classlimit_scout -1
	tf_tournament_classlimit_soldier -1
	tf_tournament_classlimit_pyro -1
	tf_tournament_classlimit_demoman -1
	tf_tournament_classlimit_heavy -1
	tf_tournament_classlimit_engineer -1
	tf_tournament_classlimit_medic -1
	tf_tournament_classlimit_sniper -1
	tf_tournament_classlimit_spy -1
	
	exec etf2l_base
	"""
	
class HighlanderBase(TextConfig):
	
	id = "etf2l_base_hl"
	script = """
	mp_tournament_whitelist "cfg/etf2l_whitelist_9v9.txt"

	tf_tournament_classlimit_scout -1
	tf_tournament_classlimit_soldier -1
	tf_tournament_classlimit_pyro -1
	tf_tournament_classlimit_demoman -1
	tf_tournament_classlimit_heavy -1
	tf_tournament_classlimit_engineer -1
	tf_tournament_classlimit_medic -1
	tf_tournament_classlimit_sniper -1
	tf_tournament_classlimit_spy -1
	
	exec etf2l_base
	"""

class Sixes5CP(TextConfig):
	
	id = "etf2l_6v6_5cp"
	script = """
	mp_maxrounds 0
	mp_timelimit 30
	mp_windifference 5
	mp_winlimit 0
	
	exec etf2l_base_6v6
	"""

class SixesKOTH(TextConfig):
	
	id = "etf2l_6v6_koth"
	script = """
	mp_maxrounds 0
	mp_timelimit 0
	mp_windifference 0
	mp_winlimit 3
	
	exec etf2l_base_6v6
	"""
	
class SixesCTF(TextConfig):
	
	id = "etf2l_6v6_ctf"
	script = """
	mp_maxrounds 0
	mp_timelimit 10
	mp_windifference 0
	mp_winlimit 5
	
	exec etf2l_base_6v6
	"""

class SixesStopwatch(TextConfig):
	
	id = "etf2l_6v6_stopwatch"
	script = """
	mp_maxrounds 0
	mp_timelimit 0
	mp_windifference 0
	mp_winlimit 0
	
	exec etf2l_base_6v6
	"""

class Highlander5CP(TextConfig):
	
	id = "etf2l_hl_5cp"
	script = """
	mp_maxrounds 0
	mp_timelimit 30
	mp_windifference 5
	mp_winlimit 0

	exec etf2l_base_hl
	"""
	
class HighlanderKOTH(TextConfig):
	
	id = "etf2l_hl_koth"
	script = """
	mp_maxrounds 0
	mp_timelimit 0
	mp_windifference 0
	mp_winlimit 3

	exec etf2l_base_hl
	"""
	
class HighlanderCTF(TextConfig):
	
	id = "etf2l_hl_ctf"
	script = """
	mp_maxrounds 0
	mp_timelimit 20
	mp_windifference 0
	mp_winlimit 7

	exec etf2l_base_hl
	"""
	
class HighlanderStopwatch(TextConfig):
	
	id = "etf2l_hl_stopwatch"
	script = """
	mp_maxrounds 0
	mp_timelimit 0
	mp_windifference 0
	mp_winlimit 0

	exec etf2l_base_hl
	"""
	
class Ultiduo(TextConfig):
	
	id = "etf2l_ultiduo"
	script = """
	mp_tournament_whitelist "cfg/etf2l_whitelist_ultiduo.txt"

	tf_tournament_classlimit_scout 0
	tf_tournament_classlimit_soldier 1
	tf_tournament_classlimit_pyro 0
	tf_tournament_classlimit_demoman 0
	tf_tournament_classlimit_heavy 0
	tf_tournament_classlimit_engineer 0
	tf_tournament_classlimit_medic 1
	tf_tournament_classlimit_sniper 0
	tf_tournament_classlimit_spy 0

	mp_maxrounds 0
	mp_timelimit 0
	mp_windifference 0
	mp_winlimit 2

	exec etf2l_base
	"""
