import collections
import enum
import functools

import venusian


class FatalError(Exception):
    """Raised for unrecoverable errors."""


class ExitStatus(enum.IntEnum):
    """Possible exit statuses for :func:`serverstf.main`."""

    OK = 0
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

    def callback(scanner, name, obj):  # pylint: disable=unused-argument

        @functools.wraps(obj)
        def wrapper(args):
            ret = obj(args)
            if ret is None:
                return ExitStatus.OK
            else:
                return ret

        scanner.subcommands.append(Subcommand(
            command, wrapper, configure_parser))

    def decorator(function):
        venusian.attach(function, callback,
                        category=__package__ + ":subcommand")
        return function

    return decorator
