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
    return scanner.subcommands


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
            else:
                return ret

        if not hasattr(scanner, "subcommands"):
            scanner.subcommands = {}
        subcommand = Subcommand(wrapper, [])
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


def argument(*args, **kwargs):
    """Add arguments to a subcommand.

    This decorator can only be applied to functions also decorated by
    :func:`subcommand`. The arguments are the exact same as one would pass
    to :meth:`argparse.ArgumentParser.add_argument`.
    """

    def callback(scanner, name, obj):
        subcommands = getattr(obj, _SUBCOMMANDS, None)
        if not subcommands:
            raise CLIError("Can't set CLI arugments for "
                           "{} as it is not a subcommand".format(obj))
        for subcommand in subcommands:
            subcommand.arguments.append((args, kwargs))

    def decorator(function):
        venusian.attach(function, callback,
                        category=__package__ + ":arguments")
        return function

    return decorator


def geoip(function):
    """Add an argument for a GeoIP database.

    This adds a mandatory ``--geoip`` argument to a subcommand. The given
    argument will be converted to a :class:`pathlib.Path`.
    """
    return argument(
        "--geoip",
        type=pathlib.Path,
        required=True,
    )(function)
