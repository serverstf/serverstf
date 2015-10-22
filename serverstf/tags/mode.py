"""Tags for game modes."""


from serverstf.tags import tag


@tag("mode:arena", ["tf2"])
def arena(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_gamemode_arena") == "1"


@tag("mode:cp", ["tf2"])
def cp(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_gamemode_cp") == "1"


@tag("mode:ctf", ["tf2"])
def ctf(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_gamemode_ctf") == "1"


@tag("mode:koth", ["tf2", "mode:cp"])
def ctf(info, players, rules, tags):
    return ("tf2" in tags
            and "mode:cp" in tags
            and info["map"].lower().startswith("koth_"))


@tag("mode:mvm", ["tf2"])
def mvm(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_gamemode_mvm") == "1"


@tag("mode:payload", ["tf2"])
def payload(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_gamemode_payload") == "1"


@tag("mode:sd", ["tf2"])
def sd(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_gamemode_sd") == "1"


@tag("mode:rd", ["tf2"])
def rd(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_gamemode_rd") == "1"


@tag("mode:medieval", ["tf2"])
def medieval(info, players, rules, tags):
    return "tf2" in tags and rules["rules"].get("tf_medieval") == "1"


@tag("mode:sb", ["tf2", "mode:arena"])
def sb(info, players, rules, tags):
    """Smash Bros mod."""
    return ("tf2" in tags
            and "mode:arena" in tags
            and info["map"].lower().startswith("sb_"))

@tag("mode:mge", ["tf2"])
def mge(info, players, rules, tags):
    return "tf2" in tags and info["map"].lower().startswith("mge_")
