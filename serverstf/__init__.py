"""The :mod:`serverstf` package.

This package implements all the services used in running a SVTF instance.
"""

import argparse
import collections
import enum
import functools
import urllib.parse

import venusian


class FatalError(Exception):
    """Raised for unrecoverable errors."""


class ExitStatus(enum.IntEnum):
    """Possible exit statuses for :func:`serverstf.main`."""

    OK = 0  # pylint: disable=invalid-name
    FATAL_ERROR = 1
    UNEXPECTED_ERROR = 2


def redis_url(raw_url):
    """Normalise a Redis URL.

    Given a URL this will ensure that it's a valid Redis URL. The only
    mandatory component is a network location.

    The scheme will be forced to ``redis``. If no port is given it will
    default to 6379. If no path is given it defaults to 0. The query and
    fragments components are ignored.

    :param str raw_url: the URL to normalise.

    :return: the normalised URL as a string.
    """
    url = urllib.parse.urlsplit(raw_url)
    if not url.hostname:
        raise argparse.ArgumentTypeError('Missing hostname or IP from URL')
    port = url.port or 6379
    network_location = "{}:{}".format(url.hostname, port)
    path = url.path or '0'
    return urllib.parse.urlunsplit(
        ('redis', network_location, path, None, None))
