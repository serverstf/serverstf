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
import logging

import redis
import valve.source.a2s
import valve.source.messages

import serverstf
import serverstf.cache
import serverstf.tags


log = logging.getLogger(__name__)


def poll(cache, tagger, address):
    """Poll the state of a server.

    This will issue a number of requests to the server at the given address
    to determine its current state. This state is then used to calculate the
    tags that should be applied to the server.

    The new state and tags are written to the cache.

    :param serverstf.cache.Cache cache: the cache to store the updated
        status in.
    :param serverstf.tags.Tagger tagger: the tagger used to determine server
        tags.
    :param servers.cache.Address address: the address of the server to poll.
    """
    log.debug("Polling %s", address)
    query = valve.source.a2s.ServerQuerier(
        (str(address.ip), address.port), timeout=5)
    try:
        info = query.get_info()
        players = query.get_players()
        rules = query.get_rules()
    except valve.source.a2s.NoResponseError as exc:
        log.warning("Timed out waiting for response from %s", address)
    except NotImplementedError as exc:
        log.error("Compressed fragments; couldn't poll %s", address)
    except valve.source.messages.BrokenMessageError as exc:
        log.exception("Seemingly broken response from %s", address)
    else:
        tags = tagger.evaluate(info, players, rules)
        cache.set(serverstf.cache.Status(
            address,
            interest=None,
            name=info["server_name"],
            map_=info["map"],
            application_id=info["app_id"],
            players=None,
            tags=tags,
        ))

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
            poll(cache, tagger, address)


def _poll_main_args(parser):
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


@serverstf.subcommand("poll", _poll_main_args)
def _poll_main(args):
    log.info("Starting poller")
    loop = asyncio.get_event_loop()
    with serverstf.cache.Cache.connect(args.url, loop) as cache:
        address = serverstf.cache.Address("151.80.218.94", 27015)
        cache.ensure(address)
        _watch(cache, args.all)
    log.info("Stopping poller")
