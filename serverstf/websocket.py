import asyncio
import logging

import websockets

import serverstf.cache


log = logging.getLogger(__name__)


class Client:

    def __init__(self, websocket, cache):
        self._websocket = websocket
        self._cache = cache

    @asyncio.coroutine
    def run(self):
        log.debug("New connection accepted")
        while True:
            received = yield from self._websocket.recv()
            if received is None:
                return
            yield from self._websocket.send(received[::-1])


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
        yield from client.run()
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
