"""Master server synchroniser.

This modules implements the service which is responsible for watching the
master server for new servers so that they can be indexed.
"""

import asyncio
import itertools
import logging

import valve.source.a2s
import valve.source.master_server

import serverstf
import serverstf.cli


log = logging.getLogger(__name__)


@serverstf.cli.subcommand("sync")
@serverstf.cli.redis
@serverstf.cli.argument(
    "regions",
    nargs="+",
    choices=("na-west", "na-east", "na", "sa",
             "eu", "as", "oc", "af", "rest", "all"),
    help="The master server region to synchronise with.",
)
@serverstf.cli.argument(
    "--forever",
    action="store_true",
    help="Attempt to synchronise continously."
)
def _sync_main(args):
    """Synchronise with the master server.

    This will poll the master server for new server addresses. These
    addresses  are then added to the cache which is identified by the
    command line arguments.

    Note that this merely adds the address to the cache. It doesn't poll
    the individual servers.

    If the ``--forever`` command line option is given, then the synchroniser
    will run continually.
    """
    log.info("Starting master server synchroniser")
    loop = asyncio.get_event_loop()
    running = itertools.repeat(True) if args.forever else iter([True, False])
    with serverstf.cache.Cache.connect(args.redis, loop) as cache:
        while next(running):
            msq = valve.source.master_server.MasterServerQuerier()
            addresses_total = 0
            addresses_new = 0
            try:
                for address in msq.find(args.regions, gamedir="tf"):
                    addresses_total += 1
                    if cache.ensure(serverstf.cache.Address(*address)):
                        addresses_new += 1
            except valve.source.a2s.NoResponseError:
                log.warning(
                    "Timed out waiting for response from the master server")
            finally:
                if addresses_total:
                    log.info("Added %i addresses to cache", addresses_new)
