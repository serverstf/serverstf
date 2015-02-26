"""Tags for server population."""

import math

from serverstf.tags import tag


@tag("population:full")
def full(info, players, rules, tags):
    # Player count can sometimes exceed max_players. This tends to be common
    # for servers which have reserved slots.
    return info["player_count"] - info["bot_count"] >= info["max_players"]


@tag("population:empty")
def empty(info, players, rules, tags):
    return info["player_count"] - info["bot_count"] == 0


@tag("population:active")
def active(info, players, rules, tags):
    return (info["player_count"] - info["bot_count"]
            >= math.floor(info["max_players"] * 0.6))
