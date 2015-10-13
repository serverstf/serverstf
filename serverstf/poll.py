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

import logging

import serverstf


log = logging.getLogger(__name__)


@serverstf.subcommand("poll")
def _poll_main(args):
    log.info("Starting poller")
    log.info("Stopping poller")
