"""Tags for server population."""

# TODO: It'd be nice to have Pylint only ignore unused-argument for `info`,
#       `players`, `rules` and `tags`. Instead of being a blanket ignore.
# pylint: disable=unused-argument

import math

from serverstf.tags import tag


@tag("population:full")
def full(info, players, rules, tags):
    """Server is full.

    Player count can sometimes exceed max_players. This tends to be common
    for servers which have reserved slots.
    """
    return info["player_count"] - info["bot_count"] >= info["max_players"]


@tag("population:empty")
def empty(info, players, rules, tags):
    """Server has no players."""
    return info["player_count"] - info["bot_count"] == 0


@tag("population:active")
def active(info, players, rules, tags):
    """At least 60% of player slots are filled."""
    return (info["player_count"] - info["bot_count"]
            >= math.floor(info["max_players"] * 0.6))
