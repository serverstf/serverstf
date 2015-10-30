"""The :mod:`serverstf` package.

This package implements all the services used in running a SVTF instance.
This module specifically includes a number of common utilities used for
defining subcommand entry-points.
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


Subcommand = collections.namedtuple(
    "Subcommand",
    (
        "name",
        "entry_point",
        "arguments",
    )
)


def subcommand(command, configure_parser=None):
    """Register a function as an application sub-command.

    Each decorated function has a Venusian callback added to the
    ``serverstf:subcommand`` category. When the callback is invoked it will
    add a :class:`Subcommand` instance to the ``subcommands`` list of the
    scanner.

    The same decorated function will be called as the entry-point of the
    subcommand if the command name was given in the command-line argument.
    The entry-point will be passed a namespace of the command-line arguments
    as parsed by argparse.

    If the subcommand needs to register additional arguments then it should
    provide a function that accepts a :class:`argparse.ArgumentParser`. This
    will be called during application start-up but before actually parsing the
    command-line arguments.

    The subcommand entry-point should return a :class:`ExitStatus`, which will
    default to :attr:`ExitStatus.OK` if it doesn't.

    :param str command: the name of the subcommand.
    """

    def callback(scanner, name, obj):  # pylint: disable=unused-argument,missing-docstring

        @functools.wraps(obj)
        def wrapper(args):  # pylint: disable=missing-docstring
            ret = obj(args)
            if ret is None:
                return ExitStatus.OK
            else:
                return ret

        scanner.subcommands.append(Subcommand(
            command, wrapper, configure_parser))

    def decorator(function):  # pylint: disable=missing-docstring
        venusian.attach(function, callback,
                        category=__package__ + ":subcommand")
        return function

    return decorator


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
