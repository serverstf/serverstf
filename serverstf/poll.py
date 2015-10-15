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

import serverstf
import serverstf.cache


log = logging.getLogger(__name__)


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
    log.info("Watching %s; all: %s", cache, all_)
    while True:
        if all_:
            addresses = cache.all_iterator()
        else:
            addresses = _interest_queue_iterator(cache)
        for address in addresses:
            log.debug(address)


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
        address = serverstf.cache.Address("0.0.0.0", 9001)
        status = serverstf.cache.Status(
            address,
            interest=0,
            name="My Fan¢y Server Name",
            map_="ctf_doublecross",
            application_id=440,
            players=None,
            tags=["mode:ctf", "population:empty"],
        )
        cache.set(status)
        cache.get(address)
        cache.subscribe(address)
        _watch(cache, args.all)
    log.info("Stopping poller")
