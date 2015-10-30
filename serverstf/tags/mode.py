"""Tags for game modes."""

# TODO: It'd be nice to have Pylint only ignore unused-argument for `info`,
#       `players`, `rules` and `tags`. Instead of being a blanket ignore.
# pylint: disable=unused-argument

from serverstf.tags import tag


@tag("mode:arena", ["tf2"])
def arena(info, players, rules, tags):
    """TF2 arena game mode."""
    return "tf2" in tags and rules["rules"].get("tf_gamemode_arena") == "1"


@tag("mode:cp", ["tf2"])
def control_point(info, players, rules, tags):
    """TF2 Control-point gamemode."""
    return "tf2" in tags and rules["rules"].get("tf_gamemode_cp") == "1"


@tag("mode:ctf", ["tf2"])
def capture_the_flag(info, players, rules, tags):
    """TF2 Capture the Flag game mode."""
    return "tf2" in tags and rules["rules"].get("tf_gamemode_ctf") == "1"


@tag("mode:koth", ["tf2", "mode:cp"])
def king_of_the_hill(info, players, rules, tags):
    """TF2 King of the Hill game mode.

    This is a derivative of the Control-point gamemode, typically indicated
    by a map starting with ``koth_``.
    """
    return ("tf2" in tags
            and "mode:cp" in tags
            and info["map"].lower().startswith("koth_"))


@tag("mode:mvm", ["tf2"])
def mann_vs_machine(info, players, rules, tags):
    """TF2 Mann vs Machine game mode."""
    return "tf2" in tags and rules["rules"].get("tf_gamemode_mvm") == "1"


@tag("mode:payload", ["tf2"])
def payload(info, players, rules, tags):
    """TF2 Payload game mode."""
    return "tf2" in tags and rules["rules"].get("tf_gamemode_payload") == "1"


@tag("mode:sd", ["tf2"])
def special_delivery(info, players, rules, tags):
    """TF2 Special Delivery game mode."""
    return "tf2" in tags and rules["rules"].get("tf_gamemode_sd") == "1"


@tag("mode:rd", ["tf2"])
def robot_destruction(info, players, rules, tags):
    """TF2 Robot Destruction game mode."""
    return "tf2" in tags and rules["rules"].get("tf_gamemode_rd") == "1"


@tag("mode:medieval", ["tf2"])
def medieval(info, players, rules, tags):
    """TF2 Medieval/Melee-only game mode."""
    return "tf2" in tags and rules["rules"].get("tf_medieval") == "1"


@tag("mode:sb", ["tf2", "mode:arena"])
def smash_bros(info, players, rules, tags):
    """Smash Bros mod."""
    return ("tf2" in tags
            and "mode:arena" in tags
            and info["map"].lower().startswith("sb_"))


@tag("mode:vsh", ["tf2", "mode:arena"])
def vs_saxton_hale(info, players, rules, tags):
    """Versus Saxton Hale.

    Official thread: https://forums.alliedmods.net/showthread.php?t=244209
    """
    return ("tf2" in tags
            and "mode:arena" in tags
            and info["map"].lower().startswith("vsh_"))


@tag("mode:dr", ["tf2", "mode:arena"])
def deathrun(info, players, rules, tags):
    """Deathrun.

    Official thread: https://forums.alliedmods.net/showthread.php?t=201623
    """
    return ("tf2" in tags
            and "mode:arena" in tags
            and info["map"].lower().startswith("dr_"))


@tag("mode:surf", ["tf2"])
def surf(info, players, rules, tags):
    """Surfing unofficial game mode."""
    return ("tf2" in tags
            and info["map"].lower().startswith("surf_"))


@tag("mode:mge", ["tf2"])
def mge(info, players, rules, tags):
    """My Gaming Edge mod game mode."""
    return "tf2" in tags and info["map"].lower().startswith("mge_")
