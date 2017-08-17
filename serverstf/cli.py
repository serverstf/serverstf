"""Utilities to define command line interfaces.

Specifically this module provides the :func:`subcommand` decorator for
defining subcommand entry-points. Arguments for these entry-points can then
be added using the :func:`argument` decorator.

In addition to the basic building blocks for creating CLIs, decorators for
commonly used arguments are also included.
"""

import argparse
import collections
import functools
import pathlib
import urllib.parse

import venusian

import serverstf


#: Name of the attribute set to indicate an object is a command entry point
_SUBCOMMANDS = "_subcommands"


class CLIError(Exception):
    """Raised for any issues configuring the command line interface."""


Subcommand = collections.namedtuple(
    "Subcommand",
    (
        "entry_point",
        "arguments",
    )
)
Subcommand.__doc__ = """\
Represents an application subcommand.

:ivar entry_point: a callable that should be called to invoke the subcommand.
:ivar arguments: a sequence of tuples containing positional and keyword
    arguments for :meth:`argparse.ArgumentParser.add_argument`.
"""


def scan(package):
    """Scan a package for subcommands.

    :param package: a module or package to scan for subcommands.

    :raise CLIError: if a subcommand name was used multiple times or there
        was an attempt to add arguments to a non-subcommand function.
    :return: a dictionary mapping subcommand names to :class:`Subcommand`s.
    """
    scanner = venusian.Scanner()
    scanner.scan(package, categories=[
        __package__ + ":subcommand",  # first so that _SUBCOMMANDS is set
        __package__ + ":arguments",
    ])
    return scanner.subcommands  # pylint: disable=no-member


def subcommand(command):
    """Register a function as a subcommand entry-point.

    Each function decorated by this function will have a :mod:`venusian`
    callback added to it so that it can be located by :func:`scan`. The
    function it self will become the :class:`Subcommand.entry_point` of the
    subcommands returned by :func:`scan`.

    There may only be one entry-point for each subcommand name.

    The decorated function should return a :class:`serverstf.ExitStatus`. If
    it doesn't it will default to :attr:`ExitStatus.OK`.

    :param str command: the name of the subcommand.
    """

    def callback(scanner, name, obj):  # pylint: disable=unused-argument,missing-docstring

        @functools.wraps(obj)
        def wrapper(args):  # pylint: disable=missing-docstring
            ret = obj(args)
            if ret is None:
                return serverstf.ExitStatus.OK
            return ret

        if not hasattr(scanner, "subcommands"):
            scanner.subcommands = {}
        subcommand = Subcommand(wrapper, [])  # pylint: disable=redefined-outer-name
        if command in scanner.subcommands:
            raise CLIError("Subcommand {!r} already defined: "
                           "{}".format(command, scanner.subcommands[command]))
        scanner.subcommands[command] = subcommand
        if not hasattr(obj, _SUBCOMMANDS):
            setattr(obj, _SUBCOMMANDS, [])
        getattr(obj, _SUBCOMMANDS).append(subcommand)

    def decorator(function):  # pylint: disable=missing-docstring
        venusian.attach(function, callback,
                        category=__package__ + ":subcommand")
        return function

    return decorator


def _add_argument(function, *args, **kwargs):
    """Add arguments to a function.

    This adds a :mod:`venusian` callback to the given function in the
    ``serverstf:arguments`` category that, when scanned, will attempt to
    add the given command line argument to the corresponding subcommand.

    :param function: the function to add the callback to. This function must
        be decorated by :func:`subcommand`.
    :param args: passed to :meth:`argparse.ArgumentParser.add_argument`.
    :param kwargs: passed to :meth:`argparse.ArgumentParser.add_argument`.

    :return: the given ``function``.
    """

    def callback(scanner, name, obj):  # pylint: disable=unused-argument,missing-docstring
        subcommands = getattr(obj, _SUBCOMMANDS, None)
        if not subcommands:
            raise CLIError("Can't set CLI arugments for "
                           "{} as it is not a subcommand".format(obj))
        for command in subcommands:
            command.arguments.append((args, kwargs))

    # Depth 2 is required so that we can use this from within decorators.
    venusian.attach(function, callback,
                    category=__package__ + ":arguments", depth=2)
    return function


def argument(*args, **kwargs):
    """Add arguments to a subcommand.

    This decorator can only be applied to functions also decorated by
    :func:`subcommand`. The arguments are the exact same as one would pass
    to :meth:`argparse.ArgumentParser.add_argument`.
    """

    def decorator(function):  # pylint: disable=missing-docstring
        return _add_argument(function, *args, **kwargs)

    return decorator


def geoip(function):
    """Add an argument for a GeoIP database.

    This adds a mandatory ``--geoip`` argument to a subcommand. The given
    argument will be converted to a :class:`pathlib.Path`.
    """
    return _add_argument(
        function,
        "--geoip",
        type=pathlib.Path,
        required=True,
    )


def _normalise_redis_url(raw_url):
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


def redis(function):
    """Add an argument for a Redis URL.

    This adds an optional ``--redis`` argument to the subcommand. The argument
    will be normalised so that the scheme, network location, port and database
    are present in the URL.

    The URL will default to ``//localhost`` normalised.
    """
    return _add_argument(
        function,
        "--redis",
        type=_normalise_redis_url,
        default="//localhost",
        help="The URL of the Redis database to use."
    )
