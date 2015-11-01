"""Master server synchroniser.

This modules implements the service which is responsible for watching the
master server for new servers so that they can be indexed.
"""

import asyncio
import logging

import serverstf
import serverstf.cli

import valve.source.a2s
import valve.source.master_server

log = logging.getLogger(__name__)


@serverstf.cli.subcommand("sync")
@serverstf.cli.argument(
    "url",
    type=serverstf.redis_url,
    nargs="?",
    default="//localhost",
    help="The URL of the Redis database to use for the cache and queues."
)
@serverstf.cli.argument(
    "--all",
    action="store_true",
    help=("When set the poller will poll all servers "
          "in the cache, not only those in the interest queue."),
)
def _sync_main(args):
    """Synchronise with the master server.

    This will continually poll the master server for new server addresses.
    These addresses are then added to the cache which is identified by the
    command line arguments.

    Note that this merely adds the address to the cache. It doesn't poll the
    individual servers.
    """
    log.info("Starting master server synchroniser")
    loop = asyncio.get_event_loop()
    with serverstf.cache.Cache.connect(args.url, loop) as cache:
        while True:
            msq = valve.source.master_server.MasterServerQuerier()
            addresses_total = 0
            addresses_new = 0
            try:
                for address in msq.find(gamedir="tf"):
                    addresses_total += 1
                    if cache.ensure(serverstf.cache.Address(*address)):
                        addresses_new += 1
            except valve.source.a2s.NoResponseError:
                log.warning(
                    "Timed out waiting for response from the master server")
            finally:
                if addresses_total:
                    log.info("Added %i addresses to cache", addresses_new)
