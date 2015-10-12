"""Handles caching of server statuses.

Server states are stored in Redis. It tracks their general info such as,
name, map, player count, etc. as well as the current players. Additionally
it maintains an index of all the tags applied to a server.

The server (ip, port) tuple is used as the key for each server.


Redis Schema:
-------------

Redis has a fairly limited type system, which means beyond the top-level
keys, everything else is stored as UTF-8 encoded byte-strings. The API however
converts transparently between more appropriate Python-native types.

When server addresses -- e.g. ("192.168.0.1", 27015) are used in Redis keys
('<address>') they are formatted into the standard colon-separated form
(e.g. 192.168.0.1:27015) and then UTF-8 encoded.

As tags are just Unicode strings, when they're used in Redis keys ('<tag>')
they are simply UTF-8 encoded.


HASH server:<address>

    - str name

        The server's name.

    - str map

        The map currently being played by the server.

    - int app

        The Steam appplication ID of the game being played. Note that this is
        the ID for the client, not the server. So for example, 440 is TF2.

    - int players

        The currenty number of players.

    - int bots

        The number of bot players.

    - int max

        The maximum number of players allowed by the server configuration.

    - json player_scores

        The player names, scores and connection durations. This fields is
        not primitive so is stored as a JSON encoded structure. The schema
        for the JSON is as follows:

        The top-level is a JSON array with zero or more objects, each with the
        following fields:

            - str name

                The player's display name.

            - int score

                The player's score.

            - timedelta duration

                The ammount of time the player has been connected to the
                server. As JSON cannot represent time deltas natively, its
                encoded as a float representing the delta in seconds.


SET server:<address>:tags

    A set maintaining the <tag>s that apply to the server.


SET tags

    A set containing all the <tag>s known to the cache.


ZSET tag:<tag>

    These sets hold any number of <address>es. For the purpose of providing
    predictable ordering this is a sorted set but the actual scoring algorithm
    is opaque.
"""

import asyncio
import functools
import inspect
import ipaddress
import logging
import urllib.parse

import asyncio_redis

import serverstf


log = logging.getLogger(__name__)


class AddressError(ValueError):
    """Exception for all errors related to :class:`Address`es."""


class CacheError(Exception):
    """Base exception for all cache related errors."""


class Address:
    """Represents a server address.

    Each server address is comprised of an IPv4 address and a port number.
    Addresses are hashable.

    :ivar ip: the :class:`ipaddress.IPv4Address` of the address.
    :ivar port: the port number for the address as an integer.

    :raises AddressError: if either the given IP address or port is invalid.
    """

    def __init__(self, ip, port):
        try:
            self.ip = ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError as exc:
            raise AddressError("Malformed IP address") from exc
        try:
            self.port = int(port)
        except TypeError as exc:
            raise AddressError("Port number is not an integer") from exc
        if self.port < 1 or self.port > 65535:
            raise AddressError("Port number is out of range")

    def __repr__(self):
        return "<{0.__class__.__name__} {0}>".format(self)

    def __str__(self):
        return "{0.ip}:{0.port}".format(self)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.ip == other.ip and self.port == other.port


class AsyncCache:
    """Asynchronous access to a Redis state cache.

    Do not instantiate this class directly. Instead use the :meth:`connect`
    coroutine.
    """
    # :ivar _connection: the :class:`asyncio_redis.Connection` to use.
    # :ivar _loop: the :mod:`asyncio` event loop to use.

    def __init__(self, connection, loop):
        self._connection = connection
        self._loop = loop

    @classmethod
    @asyncio.coroutine
    def connect(cls, url, loop):
        """Establish a connection to a Redis database.

        :param str url: the URL of the Redis database to connect to.
        :param loop: the :mod:`asyncio` event loop to use.

        :return: a new :class:`AsyncCache` instance which is bound to a Redis
            connection.
        """
        log.info("Connecting to cache at %s", url)
        url = urllib.parse.urlsplit(url)
        connection = yield from asyncio_redis.Connection.create(
            host=url.hostname,
            port=url.port,
            db=int(url.path.split("/")[1]),
            loop=loop,
        )
        return cls(connection, loop)

    @property
    def loop(self):
        """Get the event loop used by this cache."""
        return self._loop

    def close(self):
        """Close the connection to Redis.

        Once the connection is closed the object is invalidated and can no
        longer be used.
        """
        self._connection.close()

    @asyncio.coroutine
    def get(self, address):
        log.debug("Get %s", address)


class _Synchronous(type):
    """A metaclass for making an asynchronous API synchronous.

    A class using this metaclass must inherit from a base class which exposes
    a number of :mod:`asyncio.coroutine` methods. The baseclass, when
    instantiated should expose a ``loop`` attribute which is a reference to
    the :mod:`asyncio` event loop being used by that object.

    This metaclass will override the asynchronous methods so that they are
    synchronous such that their execution will block until the underlying
    asynchronous method has completed. The arguments the method accepts and
    its return value will be unmodified.

    The subclass may still explicitly override a method if needs be. In which
    case the metaclass will not override it implicitly.

    As this metaclass depends on the aforementioned ``loop`` attribute it is
    only possible for this metaclass to make instance methods synchronous
    automatically. If any asynchronous class methods are not explicitly
    overridden then a :exc:`TypeError` will be raised.
    """

    def __new__(meta, name, bases, attrs):
        for base in bases:
            for attr, member in inspect.getmembers(base):
                if asyncio.iscoroutinefunction(member):
                    if attr not in attrs:
                        # Check if the member is a class method
                        if getattr(member, "__self__", None) is base:
                            raise TypeError("The class method {!r} from {} "
                                            "must be explicitly overriden in "
                                            "{!r}".format(attr, base, name))
                        attrs[attr] = meta._make_synchronous(member)
        return super().__new__(meta, name, bases, attrs)

    @staticmethod
    def _make_synchronous(function):
        """Make a :mod:`asyncio.coroutine` wrapped function synchronous.

        Given a would-be coroutine instance method this will wrap the call in
        ``run_until_complete`` using the event loop of the object exposed as
        the ``loop`` attribute. All arguments and the return value are
        propagated.

        :param function: the coroutine function to wrap.

        :return: a synchronous wrapper around ``function``.
        """

        @functools.wraps(function)
        def synchronous(self, *args, **kwargs):
            return self.loop.run_until_complete(
                function(self, *args, **kwargs))

        return synchronous


class Cache(AsyncCache, metaclass=_Synchronous):
    """A synchronous layer on top of :class:`AsyncCache`.

    This effectively implements the exact same API as :class:`AsyncCache`.
    Each instance should be bound to an :mod:`asyncio` event loop which will
    be used for executing the underlying asynchronous operations but will
    block until they complete.

    As with :class:`AsyncCache` this class should not be instantiated
    directly. Instead, :meth:`connect` must be used.
    """

    @classmethod
    def connect(cls, url, loop):
        return loop.run_until_complete(super().connect(url, loop))


def redis_url(raw_url):
    """Normalise a Redis URL.

    Given a URL this will ensure that it's a valid Redis URL. The only
    mandatory component is a network location.

    The scheme will be forced to ``redis``. If no port is given it will
    default to 6579. If no path is given it defaults to 0. The query and
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


def cache_main_args(parser):
    parser.add_argument(
        "url",
        type=redis_url,
        nargs="?",
        default="//localhost",
        help="The URL of the Redis database to connect to."
    )


@serverstf.subcommand("cache", cache_main_args)
def cache_main(args):
    loop = asyncio.get_event_loop()
    cache = Cache.connect(args.url, loop)
    address = Address("94.23.226.212", 2055)
    try:
        cache.get(address)
    finally:
        cache.close()
