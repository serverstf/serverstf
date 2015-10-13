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

``SET serverstf/servers/<ip>:<port>/tags``
    A set containing all the tags currently applied to the server referenced
    by the key. The tags themselves are UTF-8 encoded.

``NUMBER serverstf/servers/<ip>:<port>/interest``
    This is an integer key which is used to track how much interest there is
    in a server. It is used by the interest queue to determine whether or not
    items should be re-enqueued.

``ZSET serverstf/tags/<tag>``
    These sets hold any number of server addresses (formatted as described
    above and UTF-8 encoded). Server's who's addresses are contained in one
    of these hashes is understood to have the ``<tag>`` in their own
    ``serverstf/servers/<ip>:<port>/tags`` set.

    For the purpose of providing predictable ordering this is a sorted set
    but the actual scoring algorithm is opaque.

``LIST serverstf/interesting``
    This is the *interest queue*. It is a LIST which holds UTF-8
    encoded JSON arrays. Each array has two items: an interest level and
    a stringified :class:`Address`.

    This list is actively iterated on by pollers in order to update cache
    entries for servers whose address occurs in the queue.

    The first item in the JSON array -- the interest level -- signals what
    the interest in the server was when that particular item was added to
    the queue. See :attr:`Address.interest`.
"""

import asyncio
import contextlib
import functools
import inspect
import ipaddress
import json
import logging
import urllib.parse

import asyncio_redis
import asyncio_redis.encoders

import serverstf


log = logging.getLogger(__name__)


class AddressError(ValueError):
    """Exception for all errors related to :class:`Address`es."""


class CacheError(Exception):
    """Base exception for all cache related errors."""


class EmptyQueueError(Exception):
    """Raised when attempting to pop from an empty interest queue."""


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
            self._ip = ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError as exc:
            raise AddressError("Malformed IP address") from exc
        try:
            self._port = int(port)
        except TypeError as exc:
            raise AddressError("Port number is not an integer") from exc
        if self._port < 1 or self._port > 65535:
            raise AddressError("Port number is out of range")

    def __repr__(self):
        return "<{0.__class__.__name__} {0}>".format(self)

    def __str__(self):
        return "{0.ip}:{0.port}".format(self)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        """Check another :class:`Address` for equality.

        The other address is only considered equal if both the IP address
        and port match.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.ip == other.ip and self.port == other.port

    @classmethod
    def parse(cls, address):
        """Parse an address from a string.

        This is effectively the inverse of :meth:`__str__`. The given address
        is expected to be in the ``<ip>:<port>`` form.

        :param str address: the address to parse.

        :raises AddressError: if the string is not formatted correctly or the
            address is in any other way invalid.
        :return: a new :class:`Address` instance.
        """
        split = address.split(":", 1)
        if len(split) != 2:
            raise AddressError("Addresses must be in the form <ip/host>"
                               ":<port> but got {!r}".format(address))
        return cls(*split)

    @property
    def ip(self):
        """Get the IP of the address."""
        return self._ip

    @property
    def port(self):
        """Get the port number of the address."""
        return self._port


class Status:
    """Immutable representation of the state of a server at a point in time.

    :ivar address: the :class:`Address` that identifies the server.
    :ivar interest: this is ammount of *interest* in the server's state as
        expressed as an integer. The interest correlates to the number of
        clients subscribed to the servers state. High interest levels means
        the state is updated more frequently.
    :ivar name: the display name of the server. Note that it may contain
        non-printable characters.
    :ivar map: the name of the map being played by the server.
    :ivar application_id: the Steam application ID of the game being played
        by the server. Note that this is the Steam application ID of the
        game's client not the server. For example, in the case of TF2 it is
        440 not 232250.
    :ivar tags: a frozen set of all the tags applied to the server.
    """

    def __init__(self, address, *, interest, name,
                 map_, application_id, players, tags):
        self._address = address
        self._interest = 0 if interest is None else int(interest)
        self._name = name if name is None else str(name)
        self._map = map_ if map_ is None else str(map_)
        self._application_id = application_id
        if self._application_id is not None:
            self._application_id =  int(application_id)
        self._players = players
        self.tags = frozenset(tags)

    def __repr__(self):
        return ("<{0.__class__.__name__} {0.address} "
                "({1} tags)>".format(self, len(self.tags)))

    @property
    def address(self):
        """Get the address of the server."""
        return self._address

    @property
    def interest(self):
        """Get the current interest in the server."""
        return self._interest

    @property
    def name(self):
        """Get the server name."""
        return self._name

    @property
    def map(self):
        """Get the server map."""
        return self._map

    @property
    def application_id(self):
        """Get the server Steam application ID."""
        return self._application_id

    @property
    def players(self):
        """Get the current players."""
        return self._players


class AsyncCache:
    """Asynchronous access to a Redis state cache.

    Do not instantiate this class directly. Instead use the :meth:`connect`
    coroutine.
    """
    # :ivar _connection: the :class:`asyncio_redis.Connection` to use.
    # :ivar _loop: the :mod:`asyncio` event loop to use.

    #: The encoding to use for Unicode strings.
    ENCODING = "utf-8"
    #: The root key namespace
    NAMESPACE = "serverstf"

    def __init__(self, connection, loop):
        self._connection = connection
        self._loop = loop
        self._active_iq_item = None
        self._iq_key = self._key("interesting")

    def __repr__(self):
        return "<{0.__class__.__name__} using {0._connection}>".format(self)

    @classmethod
    @asyncio.coroutine
    def connect(cls, url, loop):
        """Establish a connection to a Redis database.

        :param str url: the URL of the Redis database to connect to.
        :param loop: the :mod:`asyncio` event loop to use.

        :return: a context manager that, when entered yields a newly
            create :class:`AsyncCache` instance which is bound to a Redis
            connection.
        """
        log.info("Connecting to cache at %s", url)
        url = urllib.parse.urlsplit(url)
        connection = yield from asyncio_redis.Connection.create(
            host=url.hostname,
            port=url.port,
            db=int(url.path.split("/")[1]),
            loop=loop,
            encoder=asyncio_redis.encoders.BytesEncoder()
        )

        @contextlib.contextmanager
        def cache_context(cache):
            yield cache
            cache.close()

        return cache_context(cls(connection, loop))

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
        # Hack to work around the fact that closing the connection doesn't
        # clean upt tasks started by asyncio_redis. See:
        # https://github.com/jonathanslenders/asyncio-redis/issues/56
        self._loop.run_until_complete(asyncio.sleep(0))

    def _key(self, *parts):
        """Construct a Redis key from contituent parts.

        Each part of the key will be converted to a string before being
        joined together separated by forward slashes. Each key has an
        implicitly first part ``serverstf``. The key will be encoded as
        UTF-8.

        :return: a bytestring containing the encoded key.
        """
        key = [self.NAMESPACE]
        for part in parts:
            key.append(str(part))
        return "/".join(key).encode(self.ENCODING)

    @asyncio.coroutine
    def __get(self, address):
        """Retrieve a server status from the cache.

        :param Address address: the address of the server whose status is
            to be retrieved.

        :return: a :class:`Status` representing the current state of the
            cache for the give address.
        """
        log.debug("Get %s", address)
        key_hash = self._key("servers", address)
        key_tags = self._key("servers", address, "tags")
        key_interest = self._key("servers", address, "interest")
        transaction = yield from self._connection.multi()
        f_hash_ = yield from transaction.hgetall_asdict(key_hash)
        f_tags = yield from transaction.smembers_asset(key_tags)
        f_interest = yield from transaction.incrby(key_interest, 0)
        yield from transaction.exec()
        tags = {tag.decode(self.ENCODING) for tag in (yield from f_tags)}
        hash_ = {key.decode(self.ENCODING):
                 value.decode(self.ENCODING) for
                 key, value in (yield from f_hash_).items()}
        kwargs = {
            "interest": (yield from f_interest),
            "name": hash_.get("name"),
            "map_": hash_.get("map"),
            "application_id": None,
            "players": None,
            "tags": tags,
        }
        try:
            kwargs["application_id"] = int(hash_.get("application_id"))
        except (ValueError, TypeError) as exc:
            log.warning("Could not convert application_id "
                        "for %s to int: %s", address, exc)
        return Status(address, **kwargs)

    @asyncio.coroutine
    def __set(self, status):
        """Commit a server status to the cache.

        This sets the primary server state HASH key and the tags SET for the
        server. Both the HASH and SET are completely overridden in a MULTI
        block. If any fields on the server status are ``None`` then they will
        not be added to the hash.

        All hash fields are converted to strings and encoded as UTF-8. The
        tags are also UTF-8 encoded.

        As well as updating server-specific keys this will update the global
        tag SETs. The UTF-8 encoded stringified address is added to the new
        global tag SETs as part of the MULTI transation. For tags that have
        been removed by the new status the address is removed from the
        corresponding tag SETs outside of the transaction.

        :param Status status: the new status for the server.
        """
        address = str(status.address).encode(self.ENCODING)
        key_hash = self._key("servers", status.address)
        key_tags = self._key("servers", status.address, "tags")
        key_interest = self._key("servers", status.address, "interest")
        hash_ = {}
        for attribute in {"name", "map", "application_id"}:
            value = getattr(status, attribute)
            if value is not None:
                hash_[attribute] = str(value)
        hash_ = {key.encode(self.ENCODING):
                 value.encode(self.ENCODING) for key, value in hash_.items()}
        tags = {tag.encode(self.ENCODING) for tag in status.tags}
        transaction = yield from self._connection.multi()
        f_old_tags = yield from transaction.smembers(key_tags)
        yield from transaction.delete([key_hash, key_tags, key_interest])
        yield from transaction.incrby(key_interest, status.interest)
        yield from transaction.hmset(key_hash, hash_)
        yield from transaction.sadd(key_tags, (t for t in tags))
        for tag in status.tags:
            key_tag = self._key("tags", tag)
            yield from transaction.sadd(key_tag, [address])
        yield from transaction.exec()
        old_tags = (yield from (yield from f_old_tags).asset())
        removed_tags = old_tags - tags
        for old_tag in removed_tags:
            key_old_tag = self._key("tags", old_tag)
            yield from self._connection.srem(key_old_tag, [address])
        log.debug("Set %s with %i tags (%i removed)",
                  status.address, len(status.tags), len(removed_tags))

    @asyncio.coroutine
    def subscribe(self, address):
        """Increase the interest in an address.

        This will increase the interest for a server and add an entry in the
        interest queue for it.

        :param Address address: the address of the server to increase the
            interest for.
        """
        # TODO: fix the race condition
        status = yield from self.__get(address)
        interest = status.interest + 1
        yield from self.__set(Status(
            address,
            interest=interest,
            name=status.name,
            map_=status.map,
            application_id=status.application_id,
            players=status.players,
            tags=status.tags,
        ))
        yield from self.__push_iq(interest, address)
        log.debug("Interest in %s now %i", address, interest)

    def _encode_iq_item(self, interest, address):
        """Encode an item for the interest queue.

        The interest and stringified address are converted to a JSON array
        being being UTF-8 encoded.

        :param int interest: the interest value for the address.
        :param Address address: the server address.

        :return: a bytestring containing the encoded interest queue item.
        """
        return json.dumps([int(interest), str(address)]).encode(self.ENCODING)

    def _decode_iq_item(self, encoded):
        """Decode an item from the interest queue.

        The given item should be a UTF-8 encoded JSON array with two
        elements. The first element should be a number and the second is a
        string that will be parsed an :class:`Address`.

        :param bytes encoded: the encoded JSON array from the interest queue.

        :raises ValueError: if the queue item couldn't be decoded.
        :return: a two-tuple containing a interest value and an
            :class:`Address`.
        """
        try:
            item_decoded = json.loads(encoded.decode(self.ENCODING))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError(exc) from exc
        if not isinstance(item_decoded, list) or len(item_decoded) != 2:
            raise ValueError("Must be an array of length 2")
        interest_raw, address_raw = item_decoded
        try:
            interest = int(interest_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Interest must be an integer: %s", exc) from exc
        return interest, Address.parse(str(address_raw))

    @asyncio.coroutine
    def __push_iq(self, interest, address):
        """Push an item into the interest queue.

        The item will be encoded as a JSON array and added to the end of
        the queue.
        """
        yield from self._connection.rpush(
            self._iq_key, [self._encode_iq_item(interest, address)])

    @asyncio.coroutine
    def update_interest_queue(self):
        """Reinsert address into the interest queue.

        This should be called after calls to :meth:`interesting` in order
        reinsert the address back into the interest queue. The address is
        only reinserted if there is still sufficient interest in it.
        Otherwise this method does nothing.
        """
        interest, address = self._active_iq_item
        status = yield from self.__get(address)
        if status.interest >= interest:
            yield from self.__push_iq(interest, address)
        self._active_iq_item = None

    @asyncio.coroutine
    def interesting(self):
        """Get an address from the interest queue.

        Once finished with the address you must call
        :meth:`update_interest_queue` which will reinsert the address back
        into the queue if necessary. If not done then subsequent calls to
        this method will throw an exception.

        :raises EmptyQueueError: if the interest queue is empty.
        :return: a :class:`Address` from the interest queue.
        """
        if self._active_iq_item:
            raise CacheError("There is already an active interest queue item. "
                             "Did you forget to call update_interest_queue?")
        while self._active_iq_item is None:
            item_raw = yield from self._connection.lpop(self._iq_key)
            if not item_raw:
                raise EmptyQueueError
            try:
                self._active_iq_item = self._decode_iq_item(item_raw)
            except ValueError as exc:
                log.warning("Bad interest queue item: %s", exc)
        return self._active_iq_item[1]

    get = __get
    set = __set


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

    Additionally, name mangled methods are not overridden. This is useful
    if you need to call the asynchronous method from inside another method
    as you can expose a synchronous public API (just alias the dunder-method)
    but still call the asynchronous API internally.
    """

    def __new__(meta, name, bases, attrs):
        for base in bases:
            mangle_prefix = "_" + base.__name__ + "__"
            for attr, member in inspect.getmembers(base):
                if asyncio.iscoroutinefunction(member):
                    if (attr not in attrs
                            and not attr.startswith(mangle_prefix)):
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

    @contextlib.contextmanager
    def interesting_context(self):
        """Get an address from the interest queue.

        This encaplusates calls to :meth:`interesting` and
        :meth:`update_interest_queue` as a context manager.

        :return: an :class:`Address` from the interest queue.
        """
        yield self.interesting()
        self.update_interest_queue()
