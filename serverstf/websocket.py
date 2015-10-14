import asyncio
import itertools
import logging

import websockets

import serverstf.cache


log = logging.getLogger(__name__)


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

    def __init__(self, websocket, cache):
        self._websocket = websocket
        self._cache = cache
        self._subscriptions = []
        self._send_queue = asyncio.Queue()

    @asyncio.coroutine
    def send(self, message):
        """Enqueue a message to be sent to peer."""
        yield from self._send_queue.put(message)

    @asyncio.coroutine
    def _read(self):
        """Continually receive and handle incoming messages."""
        while True:
            received = yield from self._websocket.recv()
            if received is None:
                return
            yield from self.send(received[::-1])

    @asyncio.coroutine
    def _write(self):
        """Continually flush the send queue."""
        while True:
            message = yield from self._send_queue.get()
            yield from self._websocket.send(message)

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
            except Exception:
                log.exception("Error handling %s "
                              "in task %s", self._websocket, task)


class Service:

    #: The path the service is served from
    PATH = "/"

    def __init__(self, cache):
        self._cache = cache

    @asyncio.coroutine
    def __call__(self, websocket, path):
        if path != self.PATH:
            log.error("Client connected on path %s; dropping connection", path)
            return
        client = Client(websocket, self._cache)
        yield from client.process()
        log.debug("Connection closed")


def _websocket_args(parser):
    parser.add_argument(
        'port',
        type=int,
        help="The port the websocket service will listen on.",
    )
    parser.add_argument(
        "url",
        type=serverstf.redis_url,
        nargs="?",
        default="//localhost",
        help="The URL of the Redis database to use for the cache and queues."
    )


@asyncio.coroutine
def _websocket_async_main(args, loop):
    log.info("Starting websocket server on port %i", args.port)
    cache_context = \
        yield from serverstf.cache.AsyncCache.connect(args.url, loop)
    with cache_context as cache:
        yield from websockets.serve(Service(cache), port=args.port)
    log.info("Stopping websocket server")


@serverstf.subcommand("websocket", _websocket_args)
def _websocket_main(args):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_websocket_async_main(args, loop))
    loop.run_forever()
