"""The Pyramid application that serves the user interface."""

import logging

import pyramid.config
import waitress

import serverstf


log = logging.getLogger(__name__)


def _make_application():
    """Construct a Pyramid WSGI application.

    This creates a central Pyramid configurator then adds all routes, views
    and Jinja2 configuration to it.

    :mod:`pyramid_jinja2` is included into the configuration. The search path
    for Jinja2 is set to the ``templates/`` directory. The Jinja2 syntax is
    modified so that it uses square brackets instead of curly ones. E.g.
    ``{{foo}}`` becomes ``[[foo]]``. This applies to Jinja2 statements as
    well as comments.

    A route and view is added for ``/`` which serves the Angular application.

    Static views are added for the ``external``, ``scripts``, ``styles``,
    ``images``, ``templates`` and ``data`` directories. These are all served
    directly from the route. E.g. templates are served from ``/templates/``.

    :return: a WSGI application.
    """
    config = pyramid.config.Configurator(settings={
        "pyramid.reload_templates": True,
    })
    config.include("pyramid_jinja2")
    config.add_jinja2_search_path(__name__ + ":templates/")
    config.add_route("main", "/")
    config.add_view(route_name="main", renderer="main.jinja2")
    for static in ["external", "scripts",
                   "styles", "images", "templates", "data"]:
        config.add_static_view(static, "{}:{}/".format(__name__, static))
    config.commit()
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.block_start_string = "[%"
    jinja2_env.block_end_string = "%]"
    jinja2_env.variable_start_string = "[["
    jinja2_env.variable_end_string = "]]"
    jinja2_env.comment_start_string = "[#"
    jinja2_env.comment_end_string = "#]"
    return config.make_wsgi_app()


def _main_ui_args(parser):
    """Arguments for the ``ui`` subcommand."""
    parser.add_argument(
        "port",
        type=int,
        help="The port the UI server will listen on.",
    )
    parser.add_argument(
        "--development",
        action="store_true",
        help=("Enable extra debugging features "
              "which are not safe for production use."),
    )


@serverstf.subcommand("ui", _main_ui_args)
def _main_ui(args):
    """Run the UI WSGI application.

    This spawns a Waitress server for the application returned by
    :func:`_make_application`. It will listen on the port defined by the
    command line arguments.

    If the command line arguments specified ``--development`` then the
    ``expose_tracebacks`` option will be enabled for Waitress.
    """
    application = _make_application()
    kwargs = {
        "port": args.port,
        "threads": 1,
    }
    if args.development:
        kwargs["expose_tracebacks"] = True
    log.info("Serving UI on port %i", args.port)
    waitress.serve(application, **kwargs)
