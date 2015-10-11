"""Server state poller."""

import logging

from valve.source import a2s

import serverstf
import serverstf.cache
import serverstf.tags


log = logging.getLogger(__name__)
cache = serverstf.cache.Cache("127.0.0.1")
tagger = serverstf.tags.Tagger.scan(__package__ + ".tags")


def poll(address):
    query = a2s.ServerQuerier(address)
    info = query.get_info()
    players = query.get_players()
    rules = query.get_rules()
    tags = tagger.evaluate(info, players, rules)
    cache.set(address, {
        "name": info["server_name"],
        "map": info["map"],
        "app": info["app_id"],
        "players": info["player_count"],
        "bots": info["bot_count"],
        "max": info["max_players"],
    }, {}, tags)


@serverstf.subcommand("poll")
def poll_main(args):
    log.info("Starting poller")
    log.info("Stopping poller")
