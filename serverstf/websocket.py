"""Websocket service to access server statuses."""

import asyncio
import functools
import ipaddress
import itertools
import json
import logging

import voluptuous
import websockets

import serverstf.cache
import serverstf.cli


log = logging.getLogger(__name__)


class WebsocketError(Exception):
    """Base exception for all websocket related errors."""


class MessageError(WebsocketError):
    """Raised for message validation failures."""


def validate(schema):
    """Validate message entities against a schema.

    This is a decorator to help message handlers validate the entity against
    a :mod:`voluptuous` schema. The decorated function will raise
    :exc:`MessageError` if the entity is not valid according to the given
    schema. If the entity is valid then the wrapped function will be called
    being passed the validated entity as the sole argument.

    :param schema: a :mod:`voluptuous` schema specification.
    """

    def decorator(function):  # pylint: disable=missing-docstring
        if not asyncio.iscoroutinefunction(function):
            raise TypeError(
                "{!r} is not a coroutine function".format(function))

        @asyncio.coroutine
        @functools.wraps(function)
        def wrapper(self, entity):  # pylint: disable=missing-docstring
            try:
                validated_entity = voluptuous.Schema(schema)(entity)
            except voluptuous.Invalid as exc:
                raise MessageError("Entity: {}".format(exc)) from exc
            yield from function(self, validated_entity)

        return wrapper

    return decorator


def address_entity(value):
    """Convert a dictionary to a :class:`serverstf.cache.Address`.

    The dictionary must have an ``ip`` and ``port`` field which are a
    string and integer respectively.
    """
    return serverstf.cache.Address(**voluptuous.Schema({
        voluptuous.Required("ip"): str,
        voluptuous.Required("port"): int,
    })(value))


class Client:
    """Encapsulates a single websocket connection.

    Instances of this class handle communication to and from a connected
    client. It handles requests to subscribe to server status updates and
    then publishes to the connected peer.

    Websockets are message oriented. On the wire each message is a UTF-8
    string but this class only deals with Unicode. The messages themself
    are JSON objects. These objects are referred to as message envelopes.
    Each envelope has two fields:

    ``type``
        This is a string that identifies the type of message contained
        within the envelope.

    ``entity``
        This is the *body* of the message. Its structure is dependant on
        the message type but any JSON value is acceptable in this field.

    Communication between the server (that's us) and the client is very much
    fire and forget. It is not possible to have a request-reply model due
    to the fact that status updates may happen at any time.
    """

    def __init__(self, websocket, cache, notifier):
        self._websocket = websocket
        self._cache = cache
        self._notifier = notifier
        self._send_queue = asyncio.Queue()
        self._include = set()
        self._exclude = set()

    @asyncio.coroutine
    def send(self, type_, entity):
        """Enqueue a message to be sent to peer."""
        message = {"type": str(type_), "entity": entity}
        yield from self._send_queue.put(json.dumps(message))

    @asyncio.coroutine
    def _send_status(self, address):
        """Send a server status update.

        This will send a ``status`` type message to the client which contains
        the correct state of the server as identifier by the given address.

        The message entity is an object with the following fields:

        ``ip``
            IP address of the server as a string in dot-decimal form.

        ``port``
            Port number of server as a number.

        ``name``
            Server name as a string. Note that this may contain unprintable
            characters.

        ``map``
            Name of the currently active map.

        ``tags``
            An array of tags currently applied to the server as strings.

        ``players``
            An object describing the players on the server. This object has
            four fields of its own:

            ``current``
                The current number of players as an integer.

            ``max``
                The maximum number of players as an integer.

            ``bots``
                The number of players who are bots as an integer.

            ``scores``
                An array of three-item arrays which contain player names as a
                string, their score as a number and connection duration as
                a number in that order.

        ``country``
            The location of the server as an ISO 3166 two-letter country code.

        ``latitude``
            The location of the server in terms of latitude as a number.

        ``longitude``
            The location of the server in terms of longitude as a number.

        If the location of the server is not conclusively known then all
        location based fields (``country``, ``latitude`` and ``longitude``)
        are set to ``None``/``null``.

        The location is considered to be conclusively known if all location
        fields are not ``None``.
        """
        status = yield from self._cache.get(address)
        entity = {
            "ip": str(status.address.ip),
            "port": status.address.port,
            "name": status.name or "",
            "map": status.map or "",
            "tags": list(status.tags),
            "players": {
                "current": status.players.current,
                "max": status.players.max,
                "bots": status.players.bots,
                "scores": list([n, s, d.total_seconds()]
                               for n, s, d in status.players),
            },
            "country": None,
            "latitude": None,
            "longitude": None,
        }
        if (status.country is not None
                and status.latitude is not None
                and status.longitude is not None):
            entity["country"] = status.country
            entity["latitude"] = status.latitude
            entity["longitude"] = status.longitude
        yield from self.send("status", entity)

    @validate(address_entity)
    @asyncio.coroutine
    def _handle_subscribe(self, address):
        """Handle ``subscribe`` messages.

        This will begin watching the given address with the notifier so that
        updates will published to the client. An initial ``status`` is sent
        as well.
        """
        log.info("New subscription to address %s", address)
        yield from self._notifier.watch_server(address)
        yield from self._send_status(address)

    @validate(address_entity)
    @asyncio.coroutine
    def _handle_unsubscribe(self, address):
        """Handle ``unsubscribe`` messages.

        Stop watching the given address with the notifier.
        """
        log.info("Unsubscribing from address %s", address)
        yield from self._notifier.unwatch_server(address)

    @asyncio.coroutine
    def _send_match(self, address):
        """Notify the client that a server matches its query.

        This sends a message with type ``type``. The accompanying entity
        is an object with two fields: ``ip`` and ``port``. The ``ip`` is the
        dot-decimal IP address of the given ``address`` and the ``port`` is
        just port number as is.
        """
        yield from self.send(
            "match", {"ip": str(address.ip), "port": address.port})

    @validate({
        voluptuous.Required("include"): [str],
        voluptuous.Required("exclude"): [str],
    })
    @asyncio.coroutine
    def _handle_query(self, entity):
        """Query the cache for servers matching given tags.

        The message entity should have two fields: ``include`` and
        ``exclude``; both of which should be an array of tags as strings.
        These tags are used to query the cache to find matching servers. For
        each matching address a ``match`` message is sent.

        In addition to this we begin listening to changes to the included
        tags so that we can detect when a new server has the tag applied and
        send the appropriate ``match`` message to notify the client.
        """
        include = set(entity["include"])
        exclude = set(entity["exclude"])
        for old_tag in self._include - include:
            yield from self._notifier.unwatch_tag(old_tag)
        self._include = include
        self._exclude = exclude
        for tag in include:
            yield from self._notifier.watch_tag(tag)
        addresses = yield from self._cache.search(
            include=self._include, exclude=self._exclude)
        for address in addresses:
            yield from self._send_match(address)

    @asyncio.coroutine
    def _dispatch(self, raw_message):
        """Handle a JSON encoded message.

        This will decode the message as JSON and validate the envelope to
        ensure it has the necessary fields. If the envelope is valid then
        a method is looked up that is capable of dealing with the given
        message type.

        Message type handler methods should be named with the message type
        prefixed by ``_handle_``. For example, the handler for messages of
        type ``foo`` would be handled by :meth:`_handle_foo`.

        If a handler method exists for the message type then it will be
        called with the message entity passed in as the sole argument.

        Method handlers must be coroutine functions.

        :raises MessageError: if the message isn't JSON, the envelope
            is invalid (e.g. missing fields or wrong type) or there is no
            handler method for the given message type.
        """
        try:
            message = json.loads(raw_message)
        except ValueError as exc:
            raise MessageError("JSON: {}".format(exc)) from exc
        try:
            voluptuous.Schema({
                voluptuous.Required("type"): str,
                voluptuous.Required("entity"): lambda x: x,
            })(message)
        except voluptuous.Invalid as exc:
            raise MessageError("Envelope: {}".format(exc)) from exc
        handler = getattr(self, "_handle_" + message["type"], None)
        if not handler or not asyncio.iscoroutinefunction(handler):
            raise MessageError(
                "Unknown message type: {}".format(message["type"]))
        yield from handler(message["entity"])

    @asyncio.coroutine
    def _read(self):
        """Continually receive and handle incoming messages.

        This will continually attempt to receive messages from the websocket
        and dispatch them to appropriate handlers. When malformed messages
        are received then the client will be notified.

        If the client disconnects then the coroutine will return.
        """
        while True:
            received = yield from self._websocket.recv()
            if received is None:
                return
            try:
                yield from self._dispatch(received)
            except MessageError as exc:
                log.warning("Received bad message: %s", exc)
                yield from self.send("error", str(exc))

    @asyncio.coroutine
    def _write(self):
        """Continually flush the send queue."""
        while True:
            message = yield from self._send_queue.get()
            yield from self._websocket.send(message)

    @asyncio.coroutine
    def _watch_notifications(self):
        """Continually watch for server status updates."""
        while True:
            update, address = yield from self._notifier.watch()
            if update == self._notifier.SERVER:
                yield from self._send_status(address)
            elif update == self._notifier.TAG:
                status = yield from self._cache.get(address)
                if (status.tags <= self._include
                        and not status.tags & self._exclude):
                    yield from self._send_match(address)


    @asyncio.coroutine
    def process(self):
        """Process websocket communication.

        This starts a number of concurrent tasks which are used to read
        incoming messages and continually flush the send queue. These tasks
        will run until one of them exits (either due to an error or the
        peer disconnecting), at which point all outstanding tasks are
        cancelled and this coroutine returns.
        """
        log.debug("Handling new socket %s", self._websocket)
        done, pending = yield from asyncio.wait([
            self._read(),
            self._write(),
            self._watch_notifications(),
        ], return_when=asyncio.FIRST_COMPLETED)
        log.debug("Socket handler for %s finished", self._websocket)
        for task in itertools.chain(done, pending):
            task.cancel()
            try:
                task.result()
            except asyncio.InvalidStateError:
                # The task hasn't had chance to cancel yet but that doesn't
                # really matter.
                pass
            except Exception:  # pylint: disable=broad-except
                log.exception("Error handling %s "
                              "in task %s", self._websocket, task)


class Service:
    """The websocket service entry-point.

    This service spawns individual handlers for each client that connects.
    Clients must connect with the path ``/`` otherwise the connection is
    closed immediately.
    """

    #: The path the service is served from
    PATH = "/"

    def __init__(self, cache):
        self._cache = cache

    @asyncio.coroutine
    def __call__(self, websocket, path):
        """Handle a new socket connection.

        This spawns a :class:`Client` to handle the new connection. This
        handler will have a dedicated :class:`serverstf.cache.Notifier`
        created for it. When the client completes (either due to graceful
        disconnect or error) the notifier will be cleaned up.

        If the socket connects on a path other than ``/`` then it is
        immediately disconnected.
        """
        if path != self.PATH:
            log.error("Client connected on path %s; dropping connection", path)
            return
        notifier = yield from self._cache.notifier()
        client = Client(websocket, self._cache, notifier)
        try:
            yield from client.process()
        finally:
            notifier.close()
        log.debug("Connection closed")


@asyncio.coroutine
def _websocket_async_main(args, loop):
    """Start a websocket server.

    This will connect to the cache identified by the command line arguments
    and start websocket server to host a :class:`Service` instance. It will
    then let the socket server run indefinately.
    """
    log.info(
        "Starting websocket server on %s:%i", args.bind_host, args.bind_port)
    cache_context = \
        yield from serverstf.cache.AsyncCache.connect(args.redis, loop)
    with cache_context as cache:
        yield from websockets.serve(
            Service(cache),
            host=str(args.bind_host),
            port=args.bind_port,
            loop=loop,
        )
        # Surely this isn't the correct way to do this!?
        while True:
            yield from asyncio.sleep(1)
    log.info("Stopping websocket server")


@serverstf.cli.subcommand("websocket")
@serverstf.cli.redis
@serverstf.cli.argument(
    "--bind-host",
    type=ipaddress.IPv4Address,
    required=True,
    help="Host interface the UI server will listen on.",
)
@serverstf.cli.argument(
    "--bind-port",
    type=int,
    required=True,
    help="Port numberthe websocket service will listen on.",
)
def _websocket_main(args):
    """Start a websocket server."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_websocket_async_main(args, loop))
