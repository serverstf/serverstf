"""Master server synchroniser.

This modules implements the service which is responsible for watching the
master server for new servers so that they can be indexed.
"""

import asyncio
import logging

import serverstf

import valve.source.a2s
import valve.source.master_server

log = logging.getLogger(__name__)


def _sync_main_args(parser):
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

@serverstf.subcommand("sync", _sync_main_args)
def sync_main(args):
    log.info("Starting master server synchroniser")
    loop = asyncio.get_event_loop()
    with serverstf.cache.Cache.connect(args.url, loop) as cache:
        msq = valve.source.master_server.MasterServerQuerier()
        try:
            for address in msq.find(gamedir="tf"):
                cache.ensure(serverstf.cache.Address(*address))
        except valve.source.a2s.NoResponseError:
            pass
