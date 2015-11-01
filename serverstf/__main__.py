"""Serverstf application entry-point."""

import argparse
import logging
import sys
import time

import pkg_resources
import venusian

import serverstf


def setup_logging(level):
    """Configure the root logger.

    :param int level: the default logging level, e.g. logging.DEBUG.

    :returns: the 'serverstf' logger.
    """
    log_format = "{asctime} {levelname:8} {threadName} {name:16} {message}"
    log = logging.getLogger("")
    handler = logging.StreamHandler(stream=sys.stdout)
    format_ = logging.Formatter(fmt=log_format, style="{")
    format_.converter = time.gmtime
    handler.setFormatter(format_)
    log.setLevel(level)
    log.addHandler(handler)
    return logging.getLogger(__package__)


class LogLevelAction(argparse.Action):
    """Custom parser action to validate loglevel as either int or string."""

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            values = int(values)
        except ValueError:
            try:
                values = getattr(logging, values.upper())
            except AttributeError:
                raise argparse.ArgumentError(
                    self, "Invalid log level: {}".format(values))
        setattr(namespace, self.dest, values)


def parse_args(argv=None):
    """Parse command line arguments.

    This will scan the :mod:`serverstf` package for Venusian callbacks in the
    ``serverstf:subcommand`` category. The scanner used will have the
    ``subcommands`` attribute set to an empty list, which Venusian callbacks
    are expected to populate with :class:`svtf.Subcommand`s.

    For each subcommand, an Argprse subparser will be created. If the
    :class:`Subcommand`'s ``arguments`` argument is set it will be called being
    passed a reference to the subparser.

    The ``command`` argument will be set to the name of the subcommand that
    is to be invoked. ``command_func`` will be set to the sub-command
    entry-point function.

    A default ``--log-level`` argument is added which accepts a numeric or a
    case-insensitve symbolic name (e.g. DEBUG, INFO, etc.) log level. This
    defaults to :data`logging.INFO`.

    A version action is added for the ``--version`` argument.

    :params argv: a list of command line arguments. If ``None`` then
        ``sys.argv`` will be used.
    """
    parser = argparse.ArgumentParser(prog="serverstf")
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + pkg_resources.require(__package__)[0].version,
    )
    parser.add_argument(
        "-l", "--log-level",
        metavar="LEVEL",
        default=logging.INFO,
        help=("log verbosity; one of debug, info, warning, "
              "error or critical; or the numerical equivalent 0-100"),
        action=LogLevelAction,
    )
    # http://bugs.python.org/issue9253
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True
    scanner = venusian.Scanner()
    scanner.scan(serverstf, categories=[
        __package__ + ":subcommand",
        __package__ + ":arguments",
    ])
    for name, subcommand in scanner.subcommands.items():
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(command_func=subcommand.entry_point)
        for args, kwargs in subcommand.arguments:
            subparser.add_argument(*args, **kwargs)
    return parser.parse_args(argv)


def _main(argv=None):
    """The application mainloop.

    Parses the command-line arguments, configures the root logger and then
    delegates execution to the subcommand specified in the arguments. The
    parsed command-line arguments will be passed into the subcommand function.

    :returns: the subcommand's exit status.
    """
    args = parse_args(argv)
    setup_logging(args.log_level)
    return args.command_func(args)


def main(argv=None):
    """Application entry-point.

    :returns: an exit status.
    """
    try:
        status = _main(argv)
    except serverstf.FatalError as exc:
        logging.basicConfig(stream=sys.stdout)
        logging.log(logging.CRITICAL, exc)
        return serverstf.ExitStatus.FATAL_ERROR
    except Exception as exc:  # pylint: disable=broad-except
        logging.basicConfig(stream=sys.stdout)
        logging.exception("Unhandled exception")
        return serverstf.ExitStatus.UNEXPECTED_ERROR
    else:
        return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
