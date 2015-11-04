"""The Pyramid application that serves the user interface."""

import logging

import pyramid.authentication
import pyramid.authorization
import pyramid.config
import pyramid.security
import pyramid.session
import waitress

import openid.consumer.consumer

import serverstf
import serverstf.cli


log = logging.getLogger(__name__)
OPENID_PROVIDER = "http://steamcommunity.com/openid"


def _begin_authentication(request):
    """Begin the OpenID authentication process.

    This performs a 302 redirect to the Steam OpenID provider. The redirect
    will be configured so that upon authentication completion (whether or not
    it was successful) the user will be redirected to the
    :func:`_complete_authentication` view.
    """
    openid_request = request.openid_consumer.begin(OPENID_PROVIDER)
    location = openid_request.redirectURL(
        request.application_url,
        request.route_url("authenticate-complete"),
    )
    return pyramid.httpexceptions.HTTPFound(
        location, headers=pyramid.security.forget(request))


def _complete_authentication(request):
    """Complete the OpenID authentication process.

    This view should never be directly accessed by a user. Rather this is
    where Steam will redirect to in order to complete the OpenID
    authentication process.

    If the user signed in successfully then their Steam ID will be remembered
    and an authentication token set.
    """
    openid_response = request.openid_consumer.complete(
        request.GET, request.current_route_url())
    if openid_response.status == openid.consumer.consumer.SUCCESS:
        steam_id_64 = openid_response.identity_url.split("/")[-1]
        request.response.headers.extend(
            pyramid.security.remember(request, steam_id_64))
        return {"success": True}
    else:
        return {"success": False}


def _get_openid_consumer(request):
    """Get an OpenID consumer bound to the request's session.

    The consumer has no store because Steam's OpenID implementation is
    stateless.
    """
    return openid.consumer.consumer.Consumer(request.session, None)


def _configure_authentication(config):
    """Configure authentication policies, routes and view.

    This adds a authentication and authorisation policy to the given
    configurator. In addition to this it adds a reified request method
    called ``openid_consumer`` -- see :func:`_get_openid_consumer`.

    Two routes are added: ``authenticate-begin`` and
    ``authentication-complete``. These routes are bound to the views
    :func:`_begin_authentication` and :func:`_complete_authentication`
    respectively.

    The authentication completion view will have it's renderer set to the
    ``authentication-complete.jinja2`` Jinja template.

    Authentication it self is done through Steam's OpenID provision. The
    two views added by this function implement the OpenID flow.
    """
    # TODO: DO NOT use this factory in production!
    config.set_session_factory(
        pyramid.session.SignedCookieSessionFactory("coffeedenshul"))
    authn_policy = pyramid.authentication.AuthTktAuthenticationPolicy(
        "coffeedenshul",
        hashalg="sha512",
    )
    authz_policy = pyramid.authorization.ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(
        _get_openid_consumer,
        "openid_consumer",
        reify=True,
    )
    config.add_route("authenticate-begin", "/authenticate/begin")
    config.add_route("authenticate-complete", "/authenticate/complete")
    config.add_view(_begin_authentication, route_name="authenticate-begin")
    config.add_view(
        _complete_authentication,
        route_name="authenticate-complete",
        renderer="authentication-complete.jinja2",
    )


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
    A default 'not found' view is also added which also serves the Angular
    application. This is so that the Angular ``$location`` service can use
    *HTML5 mode* routing. Because of this there is no guarantee that a matched
    route will be set for the current request inside the entry point template.
    E.g. you can't use ``request.current_route_url``.

    Static views are added for the ``external``, ``scripts``, ``styles``,
    ``images``, ``templates`` and ``data`` directories. These are all served
    directly from the route. E.g. templates are served from ``/templates/``.

    The configuration for Steam OpenID authentication is also added.

    :return: a WSGI application.
    """
    config = pyramid.config.Configurator(settings={
        "pyramid.reload_templates": True,
    })
    config.include("pyramid_jinja2")
    config.add_jinja2_search_path(__name__ + ":templates/")
    config.add_route("main", "/")
    config.add_view(route_name="main", renderer="main.jinja2")
    config.add_notfound_view(renderer="main.jinja2")
    for static in ["external", "scripts",
                   "styles", "images", "templates", "data"]:
        config.add_static_view(static, "{}:{}/".format(__name__, static))
    _configure_authentication(config)
    config.commit()
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.block_start_string = "[%"
    jinja2_env.block_end_string = "%]"
    jinja2_env.variable_start_string = "[["
    jinja2_env.variable_end_string = "]]"
    jinja2_env.comment_start_string = "[#"
    jinja2_env.comment_end_string = "#]"
    return config.make_wsgi_app()


@serverstf.cli.subcommand("ui")
@serverstf.cli.argument(
    "port",
    type=int,
    help="The port the UI server will listen on.",
)
@serverstf.cli.argument(
    "--development",
    action="store_true",
    help=("Enable extra debugging features "
          "which are not safe for production use."),
)
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
