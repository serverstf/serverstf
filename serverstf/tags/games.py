"""Tags for specific games."""

# TODO: It'd be nice to have Pylint only ignore unused-argument for `info`,
#       `players`, `rules` and `tags`. Instead of being a blanket ignore.
# pylint: disable=unused-argument

from serverstf.tags import tag


@tag("tf2")
def tf2(info, players, rules, tags):
    """Team Fortress 2."""
    return info["app_id"] == 440


@tag("csgo")
def csgo(info, players, rules, tags):
    """Counter Strike: Global Offensive."""
    return info["app_id"] == 730
