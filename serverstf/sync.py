"""Master server synchroniser.

This modules implements the service which is responsible for watching the
master server for new servers so that they can be indexed.
"""

import logging

import serverstf


log = logging.getLogger(__name__)


@serverstf.subcommand("sync")
def sync_main(args):
    log.info("Starting master server synchroniser")
    log.info("Stopping master server synchroniser")
