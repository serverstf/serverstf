"""Handles caching of server statuses.

Server states are stored in Redis. It tracks their general info such as,
name, map, player count, etc. as well as the current players. Additionally
it maintains an index of all the tags applied to a server.

The server (ip, port) tuple is used as the key for each server.


Redis Schema:
-------------

Redis has a fairly limited type system, which means beyond the top-level
keys, everything else is stored as UTF-8 encoded byte-strings. The API however
converts transparently between more appropriate Python-native types.

When server addresses -- e.g. ("192.168.0.1", 27015) are used in Redis keys
('<address>') they are formatted into the standard colon-separated form
(e.g. 192.168.0.1:27015) and then UTF-8 encoded.

As tags are just Unicode strings, when they're used in Redis keys ('<tag>')
they are simply UTF-8 encoded.


HASH server:<address>

    - str name

        The server's name.

    - str map

        The map currently being played by the server.

    - int app

        The Steam appplication ID of the game being played. Note that this is
        the ID for the client, not the server. So for example, 440 is TF2.

    - int players

        The currenty number of players.

    - int bots

        The number of bot players.

    - int max

        The maximum number of players allowed by the server configuration.

    - json player_scores

        The player names, scores and connection durations. This fields is
        not primitive so is stored as a JSON encoded structure. The schema
        for the JSON is as follows:

        The top-level is a JSON array with zero or more objects, each with the
        following fields:

            - str name

                The player's display name.

            - int score

                The player's score.

            - timedelta duration

                The ammount of time the player has been connected to the
                server. As JSON cannot represent time deltas natively, its
                encoded as a float representing the delta in seconds.


SET server:<address>:tags

    A set maintaining the <tag>s that apply to the server.


SET tags

    A set containing all the <tag>s known to the cache.


ZSET tag:<tag>

    These sets hold any number of <address>es. For the purpose of providing
    predictable ordering this is a sorted set but the actual scoring algorithm
    is opaque.
"""


import collections

import formencode
import redis


Status = collections.namedtuple("Status", [
    "address",
    "name",
    "map",
    "app",
    "players",
    "bots",
    "max",
    "tags",
])


class _StatusSchema(formencode.Schema):

    allow_extra_fields = True
    filter_extra_fields = True

    name = formencode.validators.String(if_missing="<Unknown>")
    map = formencode.validators.String(if_missing="")
    app = formencode.validators.Int(if_missing=0)
    players = formencode.validators.Int(if_missing=0)
    bots = formencode.validators.Int(if_missing=0)
    max = formencode.validators.Int(if_missing=0)


class Cache:

    def __init__(self, host, port=6379):
        self._client = redis.StrictRedis(host, port)

    def _encode_mapping(self, mapping):
        return {str(key).encode():
            str(value).encode() for key, value in mapping.items()}

    def _decode_mapping(self, mapping):
        return {key.decode():
            value.decode() for key, value in mapping.items()}

    def key(self, address):
        return b"server:" + "{}:{}".format(*address).encode()

    def set(self, address, info, players, tags):
        info = _StatusSchema.to_python(info)
        self._client.hmset(self.key(address), self._encode_mapping(info))
        self._client.delete(self.key(address) + b":tags")
        self._client.sadd(
            self.key(address) + b":tags", *{tag.encode() for tag in tags})

    def get(self, address):
        raw_status = self._client.hgetall(self.key(address))
        raw_tags = self._client.smembers(self.key(address) + b":tags")
        status = _StatusSchema.to_python(self._decode_mapping(raw_status))
        tags = {tag.decode() for tag in raw_tags}
        return Status(address=address, tags=tags, **status)


if __name__ == "__main__":
    import rq

    import serverstf.poll

    queue = rq.Queue(connection=redis.StrictRedis())
    queue.enqueue(serverstf.poll.poll, ("94.23.226.212", 2055))
