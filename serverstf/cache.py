"""Handles caching of server statuses.

Server states are stored in Redis. It tracks their general info such as,
the server name, map, player counts and scores. Additionally it maintains
an index of all the tags applied to a server.

Each server is uniquely identified by its address which is a combination of
the IP address of the host and the port number -- these are represented by
:class:`Address` objects. These address also act as Redis keys.


Redis Schema:
-------------

Redis has a fairly limited type system meaning that the stored values are
all UTF-8 encoded strings. The API provided by this module will transparently
translate these strings to more appropriate Python types.

All keys are UTF-8 encoded. When a server address is used in a conventional
colon-separated IP-port form where the IP address it self is in the dotted
decimal format. For example: ``0.0.0.0:8000``.

Each key is prefixed by ``serverstf`` in order to act as a kind of namespace.
Key *namespaces* are separated by forward slashes. All keys are UTF-8 encoded.

``HASH serverstf/servers/<ip>:<port>``
    These hashes hold the current state of the server corresponding to the
    key. Each hash has the following keys:

    * ``name``
    * ``map``
    * ``app_id``
    * ``players``
    * ``bots``
    * ``max``
    * ``scores``

    The ``scores`` field tracks the names, connection times and scores of
    each player currently on the server. As this is a non-trivial structure
    it is stored as a JSON encoded array (still UTF-8 encoded.) The array
    itself contains further arrays, one for each player. The inner arrays
    have 3 elements: the player's display name as a string, their connection
    duration as a float in seconds and their score as an integer.

    When one of these server status hashes is retrieved from the cache it
    translated to a :class:`Status` object.

``SET serverstf/server/<ip>:<port>/tags``
    A set containing all the tags currently applied to the server referenced
    by the key. The tags themselves are UTF-8 encoded.

``ZSET serverstf/tags/<tag>``
    These sets hold any number of server addresses (formatted as described
    above and UTF-8 encoded). Server's who's addresses are contained in one
    of these hashes is understood to have the ``<tag>`` in their own
    ``serverstf/servers/<ip>:<port>/tags`` set.

    For the purpose of providing predictable ordering this is a sorted set
    but the actual scoring algorithm is opaque.
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

    @asyncio.coroutine
    def set(self, status):
        log.debug("Set %s", address)


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
    try:
        address = Address("0.0.0.0", 9001)
        cache.get(address)
    finally:
        cache.close()
