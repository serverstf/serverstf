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


def _watch(cache, passive):
    log.info("Watching %s; passive: %s", cache, passive)
    while True:
        try:
            with cache.interesting_context() as address:
                log.debug(address)
        except serverstf.cache.EmptyQueueError:
            pass

def _poll_main_args(parser):
    parser.add_argument(
        "url",
        type=serverstf.redis_url,
        nargs="?",
        default="//localhost",
        help="The URL of the Redis database to use for the cache and queues."
    )
    parser.add_argument(
        "--passive",
        action="store_true",
        help=("When set the poller will poll all servers "
              "in the cache, not only those in the interest queue."),
    )


@serverstf.subcommand("poll", _poll_main_args)
def _poll_main(args):
    log.info("Starting poller")
    cache = serverstf.cache.Cache.connect(args.url, asyncio.get_event_loop())
    try:
        _watch(cache, args.passive)
    finally:
        cache.close()
    log.info("Stopping poller")
