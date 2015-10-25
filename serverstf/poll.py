"""Server state poller.

This module implements the ``poll`` subcommand which is a simple service
that takes responsibility for keeping the server state cache up to date.

It watches a Redis list for :class:`serverstf.cache.Address`es to poll.
When a server is polled A2S requests are issued to it and the tags are
re-evaluated. This updated state is then comitted to the cache.

The poller has two modes: normal and passive. In the normal mode the poller
watches the so-called 'interest queue'. The interest queue is a kind of
priority queue where the ammount of *interest* in an address determines how
many occurrences of it there is the queue and hence controls how frequently
it gets polled.

In passive mode the poller simply polls all servers known to the cache.
This is done in an attempt to prevent cache states becoming too stale if
they're not in the interest queue.
"""

import asyncio
import datetime
import logging

import valve.source.a2s
import valve.source.messages

import serverstf
import serverstf.cache
import serverstf.tags


log = logging.getLogger(__name__)


class PollError(Exception):
    """Exception raised for all polling errors."""


def poll(tagger, address):
    """Poll the state of a server.

    This will issue a number of requests to the server at the given address
    to determine its current state. This state is then used to calculate the
    tags that should be applied to the server.

    :param serverstf.tags.Tagger tagger: the tagger used to determine server
        tags.
    :param servers.cache.Address address: the address of the server to poll.

    :raise PollError: if the server is unreachable or does not return a
        valid response.
    :return: a :class:`serverstf.cache.Status` containing the up-to-date
        state of the server.
    """
    log.debug("Polling %s", address)
    query = valve.source.a2s.ServerQuerier(
        (str(address.ip), address.port), timeout=5)
    try:
        info = query.get_info()
        players = query.get_players()
        rules = query.get_rules()
    except valve.source.a2s.NoResponseError as exc:
        raise PollError("Timed out waiting for "
                        "response from {}".format(address)) from exc
    except NotImplementedError as exc:
        raise PollError("Compressed fragments; "
                        "couldn't poll {}".format(address)) from exc
    except valve.source.messages.BrokenMessageError as exc:
        raise PollError(
            "Seemingly broken response from {}".format(address)) from exc
    else:
        tags = tagger.evaluate(info, players, rules)
        scores = []
        for entry in players["players"]:
            # For newly connected players there is a delay before their name
            # becomes available to the server, so we just filter these out.
            if entry["name"]:
                duration = datetime.timedelta(seconds=entry["duration"])
                scores.append((entry["name"], entry["score"], duration))
        players_status = serverstf.cache.Players(
            current=info["player_count"],
            max_=info["max_players"],
            bots=info["bot_count"],
            scores=scores,
        )
        return serverstf.cache.Status(
            address,
            interest=None,
            name=info["server_name"],
            map_=info["map"],
            application_id=info["app_id"],
            players=players_status,
            tags=tags,
        )

def _interest_queue_iterator(cache):
    """Expose a cache's interest queue as an iterator.

    .. note::
        It is possible the generator returned by function can never be
        exhausted.
    """
    while True:
        try:
            with cache.interesting_context() as address:
                yield address
        except serverstf.cache.EmptyQueueError:
            return


def _watch(cache, all_):
    """Poll servers in the cache.

    This will poll servers in the cache updating their statuses as it goes.
    Either the interest queue or entire cache is used to determining which
    servers to poll.

    :param serverstf.cache.Cache cache: the server status cache to poll and
        write updates to.
    :param bool all_: if ``True`` then every server in the cache will be
        polled. Otherwise only servers which exist in the internet queue
        will be.
    """
    log.info("Watching %s; all: %s", cache, all_)
    tagger = serverstf.tags.Tagger.scan(__package__)
    while True:
        if all_:
            addresses = cache.all_iterator()
        else:
            addresses = _interest_queue_iterator(cache)
        for address in addresses:
            try:
                status = poll(tagger, address)
            except PollError as exc:
                log.error("Couldn't poll {}: {}".format(address, exc))
            else:
                cache.set(status)


def _poller_main_args(parser):
    parser.add_argument(
        "url",
        type=serverstf.redis_url,
        nargs="?",
        default="//localhost",
        help="The URL of the Redis database to use for the cache and queues."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=("When set the poller will poll all servers "
              "in the cache, not only those in the interest queue."),
    )


@serverstf.subcommand("poller", _poller_main_args)
def _poller_main(args):
    log.info("Starting poller")
    loop = asyncio.get_event_loop()
    with serverstf.cache.Cache.connect(args.url, loop) as cache:
        _watch(cache, args.all)
    log.info("Stopping poller")


def _poll_main_args(parser):
    parser.add_argument(
        "address",
        type=serverstf.cache.Address.parse,
        help="The address of the server to poll in the <ip>:<port> form."
    )


@serverstf.subcommand("poll", _poll_main_args)
def _poll_main(args):
    tagger = serverstf.tags.Tagger.scan(__package__)
    try:
        status = poll(tagger, args.address)
    except PollError as exc:
        raise serverstf.FatalError from exc
    else:
        players = sorted(status.players, key=lambda p: p[1], reverse=True)
        print("\nStatus\n------")
        print("Address:", status.address)
        print("App:    ", status.application_id)
        print("Name:   ", status.name)
        print("Map:    ", status.map)
        print("Tags:   ")
        for tag in sorted(status.tags):
            print(" -", tag)
        print("Players:",
              "{0.current}/{0.max} ({0.bots} bots)".format(status.players))
        for name, score, duration in players:
            print(" -", str(duration).split(".")[0], str(score).rjust(4), name)
