import asyncio
import json
import logging
import sys

import venusian
import websockets

import serverstf.cache


log = logging.getLogger(__name__)


class ServiceError(Exception):
    pass


class Service:

    def __init__(self):
        self._handlers = {}
        self._buffer = []
        scanner = venusian.Scanner(service=self)
        scanner.scan(sys.modules[__package__], categories=["svtf.handlers"])

    def register_handler(self, type_, handler):
        if type_ not in self._handlers:
            self._handlers[type_] = []
        self._handlers[type_].append(handler)

    def _parse_message(self, message):
        parsed = json.loads(message)
        if "type" not in parsed:
            raise ServiceError("Message envelope missing 'type' field")
            if not isinstance(pared["type"], str):
                raise ServiceError(
                    "Envelope 'type' field is the wrong type, "
                    "expected str got {}".format(type(parsed["type"])))
        if "entity" not in parsed:
            raise ServiceError("Message envelope missing 'entity' field")
        return parsed["type"], parsed["entity"]

    @asyncio.coroutine
    def _dispatch(self, type_, entity):
        if type_ not in self._handlers:
            raise ServiceError("Unknown message type {!r}".format(type_))
        for handler in self._handlers[type_]:
            response = yield from handler(entity)
            self.send(*response)

    def send(self, type_, entity):
        self._buffer.append(json.dumps({"type": type_, "entity": entity}))

    @staticmethod
    def handler(type_):

        def callback(scanner, name, obj):
            scanner.service.register_handler(type_, asyncio.coroutine(obj))

        def wrapper(function):
            venusian.attach(function, callback, category="svtf.handlers")
            return function

        return wrapper

    @asyncio.coroutine
    def __call__(self, websocket, path):
        while True:
            message = yield from websocket.recv()
            if message is None:
                return
            type_, entity = self._parse_message(message)
            try:
                yield from self._dispatch(type_, entity)
            except ServiceError as exc:
                self.send("error", str(exc))
            for outgoing in self._buffer:
                yield from websocket.send(outgoing)
            del self._buffer[:]


@Service.handler("hello")
def hello_handler(entity):
    return "hello", "world"


@Service.handler("subscribe")
def subcribe(address):
    state = yield from serverstf.cache.get(("94.23.226.212", 2055))
    response = {
        "address": {
            "ip": state.address[0],
            "port": state.address[1],
        },
        "name": state.name,
        "map": state.map,
        "players": {
            "real": state.players,
            "bots": state.bots,
            "max": state.max,
        },
        "tags": list(state.tags),
    }
    return "status", response


def websocket_args(parser):
    parser.add_argument(
        'port',
        type=int,
        help="The port the websocket service will listen on.",
    )


@serverstf.subcommand("websocket", websocket_args)
def websocket_main(args):
    log.info("Starting websocket server on port %i", args.port)
    server = websockets.serve(Service(), "0.0.0.0", args.port)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
    log.info("Stopping websocket server")
