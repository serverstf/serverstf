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
Key *namespaces* are separated by forward slashes.

``SET serverstf/servers``
    A set containing the addresses of all the servers in the cache. This is
    the authorative list of all servers tracked by the cache. The addresses
    themselves are just UTF-8 encoded string representations of
    :class:`Address`es.

``HASH serverstf/servers/<ip>:<port>``
    These hashes hold the current state of the server corresponding to the
    key. Each hash has the following keys:

    * ``name``
    * ``map``
    * ``application_id``
    * ``players``

    The ``players`` field tracks the players on the server. Include the
    current number of players, the maximum allowed, how many are boths and
    each individual player's name, score and connection time.

    As this is a non-trivial structure it is stored as a JSON object (still
    UTF-8 encoded.) The object contains four fields:

    ``current``
        The current number of players.

    ``max``
        The maximum number of players supported by the server.

    ``bots``
        The number of players that are bots.

    ``scores``
        An array of three-item arrays which contains (in the following order)
        the player name as a string, their score as a number and their
        connection duration in seconds as a float.

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
import datetime
import functools
import inspect
import ipaddress
import json
import logging
import uuid
import urllib.parse

import asyncio_redis
import asyncio_redis.encoders

import serverstf


log = logging.getLogger(__name__)


class AddressError(ValueError):
    """Exception for all errors related to :class:`Address`es."""


class PlayersError(ValueError):
    """Exception raised for invalid :class:`Players` objects."""


class NotifierError(Exception):
    """Exception raised for all errors stemming from :class:`Notifier`s."""


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


class Players:
    """Immutable representation of the server players at a point in time.

    :ivar current: the current number of players as an integer.
    :ivar max: the maximum number of players supported by the server as an
        integer.
    :ivar bots: the current number of players that are bots as an integer.

    :param scores: an iterable of three-item tuples containing the player's
        name as a string, their score as an integer and their connection
        duration as a :class:`datetime.timedelta`.
    """

    def __init__(self, *, current, max_, bots, scores):
        self._current = int(current)
        self._max = int(max_)
        self._bots = int(bots)
        normalised_scores = []
        for name, score, duration in scores:
            name = str(name)
            score = int(score)
            if not isinstance(duration, datetime.timedelta):
                raise PlayersError("Player connection duration must "
                                   "be a {} object".format(datetime.timedelta))
            normalised_scores.append((name, score, duration))
        self._scores = tuple(normalised_scores)

    def __repr__(self):
        return ("<{0.__class__.__name__} "
                "{0.current}/{0.max} ({0.bots} bots)>".format(self))

    def __iter__(self):
        """Iterate over players and scores.

        When iterated on this yields a tuple for each connected player
        containing their name, score and connection duration. The players
        themselves should never be considered to be in any particular order.

        .. note::
            It's possible for the number of players returned by this iterator
            to be less than or greater than that of the :attr:`current`
            players.
        """
        return iter(self._scores)

    @property
    def current(self):
        """Get the current number of players."""
        return self._current

    @property
    def max(self):
        """Get the maximum number of players."""
        return self._max

    @property
    def bots(self):
        """Get the current number of NPC players."""
        return self._bots

    @classmethod
    def from_json(cls, encoded):
        """Parse a JSON-encoded object.

        This is effectively the inverse of :meth:`to_json`.

        :raises PlayersError: if the JSON or the structure of the JSON object
            is invalid in any way.
        :return: a new :class:`Players`.
        """
        try:
            decoded = json.loads(encoded)
        except ValueError as exc:
            raise PlayersError("Bad JSON: {}".format(exc)) from exc
        for field in ["current", "max", "bots", "scores"]:
            if field not in decoded:
                raise PlayersError("Missing field {!r}".format(field))
        try:
            current = int(decoded["current"])
            max_ = int(decoded["max"])
            bots = int(decoded["bots"])
        except (ValueError, TypeError) as exc:
            raise PlayersError(
                "Malformed integer fields: {}".format(exc)) from exc
        else:
            scores = []
            for entry in decoded["scores"]:
                if not isinstance(entry, list) or not len(entry) == 3:
                    raise PlayersError(
                        "Malformed scores; expected list "
                        "of length 3 but got: {!r}".format(entry))
                if not isinstance(entry[0], str):
                    raise PlayersError("First item must be a string "
                                       "for but got: {!r}".format(entry[0]))
                if not all(isinstance(i, (int, float)) for i in entry[1:]):
                    raise PlayersError("Last two items must be numbers "
                                       "but got: {!r}".format(entry[1:]))
                scores.append((entry[0],  entry[1],
                               datetime.timedelta(seconds=entry[2])))
            return cls(current=current, max_=max_, bots=bots, scores=[])


    def to_json(self):
        """Convert the players to a JSON-encoded object.

        The JSON object will have four fields: ``current``, ``max``, ``bots``
        and ``scores``. The first three are just plain numbers corresponding
        to the attributes of the same names. ``scores`` is an array of
        arrays which contain the name, score and duration (in seconds) of
        each player.

        :return: a string containing the JSON-encoded object.
        """
        object_ = {
            "current": self.current,
            "max": self.max,
            "bots": self.bots,
            "scores": [],
        }
        for name, score, duration in self:
            object_["scores"].append([name, score, duration.total_seconds()])
        return json.dumps(object_)


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
    :ivar players: a :class:`Players` instance containing all the players
        currently on the server. Defaults to an empty :class:`Players` object
        if not set.
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
        if players is None:
            players = Players(current=0, max_=0, bots=0, scores=[])
        if not isinstance(players, Players):
            raise TypeError("Status players must be "
                            "a {} instance or None".format(Players))
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


class Notifier:
    """Send and receive notifications about cache state changes.

    This class wraps the Redis pub/sub subsystem to provide a method for
    signaling when the cache's state changes. It also allows other services
    to listen for these changes.

    You should never instantiate this class directly, instead use
    :meth:`AsyncCache.notifier`. These notifier objects are strictly
    asynchronous and therefore public use of them is not possible with
    synchronous caches.

    When a notifier is used to listen for notifications it enters the
    *watching* state. In this state it is not possible to use the same
    notifier to send notifications. This is a limitation of the Redis
    pub/sub system. Any attempts to send notifcations whilst in this state
    will result in :exc:`NotifierError`.
    """

    SERVER = "servers"
    TAG = "tags"

    def __init__(self, connection, encoding, namespace):
        self._connection = connection
        self._encoding = encoding
        self._namespace = namespace
        self._subscriber = None

    @property
    def watching(self):
        """Determine if the notifier is in watching mode."""
        return self._subscriber is not None

    def close(self):
        """Close the Redis connection."""
        self._connection.close()

    def _channel(self, *parts):
        """Construct a Redis pub/sub channel name from contituent parts.

        :return: a bytestring containing the encoded channel name.
        """
        channel = [self._namespace, "channels"]
        for part in parts:
            channel.append(str(part))
        return "/".join(channel).encode(self._encoding)

    @asyncio.coroutine
    def _get_subscriber(self):
        """Get the :mod:`asyncio_redis` subscriber.

        This will put the Redis connection in pub/sub mode making it
        impossible send most commands and hence the notifier enteres the
        *watching* state.

        :return: a :class:`asyncio_redis.Subscription`.
        """
        if not self._subscriber:
            self._subscriber = yield from self._connection.start_subscribe()
        return self._subscriber

    @asyncio.coroutine
    def notify_server(self, address):
        """Send a notification of server status update.

        This publishes a UTF-8 encoded stringified version of the given
        address to a channel dedicated to that address.

        :param Address address: the address to send the notification for.

        :raises NotifierError: if the notifier has entered watching mode.
        """
        if self.watching:
            raise NotifierError(
                "Notifier in watch mode; cannot send notifications")
        channel_server = self._channel(self.SERVER, address)
        log.debug("Publish %s", channel_server)
        yield from self._connection.publish(
            channel_server, str(address).encode(self._encoding))

    @asyncio.coroutine
    def notify_tag(self, tag, address):
        """Send a notification of a server being added to a tag.

        This publishes a UTF-8 encoded stringified version of the given
        address to a channel dedicated to the tag.
        """
        if self.watching:
            raise NotifierError(
                "Notifier in watch mode; cannot send notifications")
        channel_server = self._channel(self.TAG, address)
        log.debug("Publish %s", channel_server)
        yield from self._connection.publish(
            channel_server, str(address).encode(self._encoding))

    @asyncio.coroutine
    def watch_server(self, address):
        """Watch for server status updates.

        :param Address address: the address of the server to subscribe to
            updates for.
        """
        channel_server = self._channel(self.SERVER, address)
        subscriber = yield from self._get_subscriber()
        yield from subscriber.subscribe([channel_server])
        log.debug("Subscribed to %s", channel_server)

    @asyncio.coroutine
    def unwatch_server(self, address):
        """Stop watching for server status updates.

        This is the inverse of :meth:`watch_server`.
        """
        channel_server = self._channel(self.SERVER, address)
        subscriber = yield from self._get_subscriber()
        yield from subscriber.unsubscribe([channel_server])
        log.debug("Unsubscribed from %s", channel_server)

    @asyncio.coroutine
    def watch_tag(self, tag):
        """Watch a tag for updates."""
        channel_server = self._channel(self.TAG, tag)
        subscriber = yield from self._get_subscriber()
        yield from subscriber.subscribe([channel_server])
        log.debug("Subscribed to %s", channel_server)

    @asyncio.coroutine
    def unwatch_tag(self, tag):
        """Stop watching a tag for updates."""
        channel_server = self._channel(self.TAG, address)
        subscriber = yield from self._get_subscriber()
        yield from subscriber.unsubscribe([channel_server])
        log.debug("Unsubscribed from %s", channel_server)

    @asyncio.coroutine
    def watch(self):
        """Wait for server status or tag updates.

        This coroutine will block until a notification has been published
        for a server or tag that is being actively watched. If the notifier
        is not currently watching any servers (e.g. no calls
        :meth:`watch_server` of :meth:`watch_tag` have been made) then the
        coroutine will wait indefinately.

        :return: a tuple containing the type of update (either :attr:`SERVER`
            or :attr:`TAG`) and a corresponding :class:`Address`.
        """
        subscriber = yield from self._get_subscriber()
        address = None
        while not address:
            message = yield from subscriber.next_published()
            type_ = message.channel.decode(self._encoding).split("/")[-2]
            try:
                address = Address.parse(message.value.decode(self._encoding))
            except (UnicodeDecodeError, AddressError) as exc:
                log.error("Malformed address on channel "
                          "%s: %s: %s", message.channel, message.value, exc)
        return type_, address


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
        self._notifier = None
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
            encoder=asyncio_redis.encoders.BytesEncoder(),
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
        # clean up tasks started by asyncio_redis. See:
        # https://github.com/jonathanslenders/asyncio-redis/issues/56
        if not self._loop.is_running():
            self._loop.run_until_complete(asyncio.sleep(0))

    @asyncio.coroutine
    def __internal_notifier(self):
        """Get the internal notifier used for publishing changes.

        The return value is cached so that subsequent calls always return
        same notifier.

        :return: a :class:`Notifier`.
        """
        if not self._notifier:
            self._notifier = yield from self.__notifier()
        return self._notifier

    @asyncio.coroutine
    def __notifier(self):
        """Get a notifier for the cache.

        :return: a :class:`Notifier` object connected to the same Redis
            database as the cache.
        """
        connection = yield from asyncio_redis.Connection.create(
            host=self._connection.host,
            port=self._connection.port,
            db=self._connection.protocol.db,
            loop=self._loop,
            encoder=asyncio_redis.encoders.BytesEncoder(),
        )
        return Notifier(connection, self.ENCODING, self.NAMESPACE)

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

    def _random_key(self):
        """Construct a random Redis key.

        This will create a normal key (see :meth:`_key`) using a random UUID
        so it's safe to use for temporary usage.

        :return: a bytestring containing the encoded key.
        """
        return self._key("random", uuid.uuid4())

    @asyncio.coroutine
    def __ensure(self, address):
        """Ensure the address exists in the authorative set.

        The address is stringified and UTF-8 encoded before being added to
        the authorative set.

        :param Address address: the address to add to the cache.

        :return: ``True`` if the address didn't already exist in the cache,
            ``False`` otherwise.
        """
        added = yield from self._connection.sadd(
            self._key("servers"), [str(address).encode(self.ENCODING)])
        return added == 1

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
        try:
            kwargs["players"] = Players.from_json(hash_.get("players", ""))
        except PlayersError as exc:
            log.warning("Could not decode players "
                        "JSON object for %s: %s", address, exc)
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

        Note that the :attr:`Status.interest` field is ignored when setting
        the state.

        :param Status status: the new status for the server.
        """
        address = str(status.address).encode(self.ENCODING)
        key_hash = self._key("servers", status.address)
        key_tags = self._key("servers", status.address, "tags")
        hash_ = {}
        for attribute in {"name", "map", "application_id"}:
            value = getattr(status, attribute)
            if value is not None:
                hash_[attribute] = str(value)
        hash_["players"] = status.players.to_json()
        hash_ = {key.encode(self.ENCODING):
                 value.encode(self.ENCODING) for key, value in hash_.items()}
        tags = {tag.encode(self.ENCODING) for tag in status.tags}
        yield from self.__ensure(status.address)
        transaction = yield from self._connection.multi()
        f_old_tags = yield from transaction.smembers(key_tags)
        yield from transaction.delete([key_hash, key_tags])
        yield from transaction.hmset(key_hash, hash_)
        yield from transaction.sadd(key_tags, (t for t in tags))
        for tag in status.tags:
            key_tag = self._key("tags", tag)
            yield from transaction.sadd(key_tag, [address])
        yield from transaction.exec()
        notifier = yield from self.__internal_notifier()
        yield from notifier.notify_server(status.address)
        old_tags = (yield from (yield from f_old_tags).asset())
        removed_tags = old_tags - tags
        for old_tag in removed_tags:
            key_old_tag = self._key("tags", old_tag)
            yield from self._connection.srem(key_old_tag, [address])
        new_tags = tags - old_tags
        for tag in new_tags:
            yield from notifier.notify_tag(
                tag.decode(self.ENCODING), status.address)
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
        key_interest = self._key("servers", address, "interest")
        interest = yield from self._connection.incr(key_interest)
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

    @asyncio.coroutine
    def __fetch_addresses_from_cursor(self, cursor, queue):
        """Fetch addresses from a Redis cursor.

        This will read all available values from a Redis cusor, convert them
        to :class:`Address` and then place them into a asynchronous queue
        returning when the end of the cursor is reached.

        The cursor is expected to yield UTF-8 encoded stringified
        :class:`Address`es.

        :param asyncio.cursors.Cursor cursor: the Redis cursor to fetch
            results from.
        :param FiniteAsyncQueue queue: the queue to place :class:`Address`es
            in.
        """
        with queue:
            while True:
                item = yield from cursor.fetchone()
                if item is None:
                    return
                try:
                    yield from queue.put(
                        Address.parse(item.decode(self.ENCODING)))
                except (UnicodeDecodeError, AddressError) as exc:
                    log.warning("Bad address from cursor %s: %s", cursor, exc)

    @asyncio.coroutine
    def all(self):
        """Get all the addresses in the cache.

        This returns a queue which will be populated by addresses that are
        held by the cache.

        :return: a :class:`FiniteAsyncQueue` containing :class:`Address`es.
        """
        key = self._key("servers")
        queue = FiniteAsyncQueue(loop=self._loop)
        cursor = yield from self._connection.sscan(key)
        asyncio.Task(self.__fetch_addresses_from_cursor(cursor, queue))
        return queue

    @asyncio.coroutine
    def search(self, *, include=None, exclude=None):
        """Search for addresses by tags.

        :param include: a sequence of tags that addresses must have.
        :param exclude: a sequence of tags that will be used to filter the
            the set of addresses.

        :return: a set of :class:`Address`es that match the query.
        """
        key_intersection = self._random_key()
        key_include = [self._key("tags", tag) for tag in include or []]
        key_exclude = [self._key("tags", tag) for tag in exclude or []]
        if not key_include:
            return set()
        try:
            yield from self._connection.sinterstore(
                key_intersection, key_include)
            raw_addresses = yield from self._connection.sdiff_asset(
                [key_intersection] + key_exclude)
        finally:
            yield from self._connection.delete([key_intersection])
        addresses = set()
        for raw_address in raw_addresses:
            try:
                address = Address.parse(raw_address.decode(self.ENCODING))
            except (UnicodeDecodeError, AddressError):
                # can't do much here, not even log which key it came from
                pass
            else:
                addresses.add(address)
        return addresses

    notifier = __notifier
    ensure = __ensure
    get = __get
    set = __set


class EndOfQueueError(Exception):
    """Raised when the end of a :class:`FiniteAsyncQueue` is reached."""


class FiniteAsyncQueue(asyncio.Queue):
    """A finite/closable asynchronous queue.

    This is the exact same as :class:`asyncio.Queue` except that the queue
    can be *closed*. When the queue is closed and exhausted and further
    attempts to get items from the queue will raise an exception.

    Instances of this class are context managers. When exited the queue
    is closed meaning that once all items have been removed from the
    queue future calls to :meth:`get` or :meth:`get_nowait` raise
    :exc:`EndOfQueueError`.
    """

    def __init__(self, *, loop=None):
        super().__init__(loop=loop)
        self._closed = False
        self._end_of_queue = object()

    def __enter__(self):
        pass

    def __exit__(self, type_, value, traceback):
        self.put_nowait(self._end_of_queue)
        self._closed = True

    def _check_end_of_queue(self, item):
        if item is self._end_of_queue:
            raise EndOfQueueError
        return item

    @asyncio.coroutine
    def get(self):
        return self._check_end_of_queue((yield from super().get()))

    def get_nowait(self):
        return self._check_end_of_queue(super().get_nowait())

    @asyncio.coroutine
    def put(self, item):
        if self._closed:
            raise EndOfQueueError
        yield from super().put(item)


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

    def notifier(self):
        raise NotImplementedError(
            "Notifiers not available for synchronous caches.")

    @contextlib.contextmanager
    def interesting_context(self):
        """Get an address from the interest queue.

        This encaplusates calls to :meth:`interesting` and
        :meth:`update_interest_queue` as a context manager.

        :return: an :class:`Address` from the interest queue.
        """
        yield self.interesting()
        self.update_interest_queue()

    def all(self):
        """Use :meth:`all_iterator` for the synchronous implementation."""
        raise NotImplementedError("Use all_iterator instead")

    def all_iterator(self):
        """Get an iterator of all addresses in the cache.

        This is a synchronous version of :meth:`all` which wraps a
        :class:`FiniteAsyncQueue` in an interator. The iterator will
        complete once the end of the queue is reached.

        :return: an iterator of :class:`Address`es.
        """
        queue = self.loop.run_until_complete(super().all())
        while True:
            # Give time to the event loop so cursor reads have time to
            # complete.
            self.loop.run_until_complete(asyncio.sleep(0))
            try:
                yield queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            except EndOfQueueError:
                return
