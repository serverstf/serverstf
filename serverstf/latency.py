"""Calculate and plot distance-latency curves.

This module provides utilties to collect data for and generate a linear
regression that can be used to approximate server latency based on the
distance to it.

Specifically this module provides the ``ping`` and ``ping-plot`` subcommands.
The former collects the raw data by pinging every server in the given cache
and writes it to file. The latter plots this data using Bokeh.
"""

import asyncio
import concurrent.futures
import contextlib
import functools
import json
import logging
import math
import multiprocessing
import pathlib
import tempfile
import threading

import bokeh.plotting
import valve.source.a2s

import serverstf.cache
import serverstf.cli


log = logging.getLogger(__name__)
EARTH_RADIUS = 6371000  # metres


class PingError(Exception):
    """Raised if unable to ping a server."""


def _distance(origin, target):
    """Calculate the distance between two points on Earth.

    :param origin: a two-tuple containing latitude and longitude.
    :param target: a two-tuple containing latitude and longitude.

    :return: the distance between the two points in metres.
    """
    o_latitude, o_longitude = (math.radians(o) for o in origin)
    t_latitude, t_longitude = (math.radians(t) for t in target)
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(
        math.pow(math.sin((o_latitude - t_latitude) / 2), 2) +
        math.cos(t_latitude) *
        math.cos(o_latitude) *
        math.pow(math.sin((o_longitude - t_longitude) / 2), 2)
    ))


def _ping(address):
    """Ping a server.

    :param serverstf.cache.Address address: the address of the server to ping.

    :return: the ping to the server in seconds.
    """
    query = valve.source.a2s.ServerQuerier(
        (str(address.ip), address.port), timeout=1.0)
    try:
        return query.ping() / 1000.0
    except valve.source.a2s.NoResponseError as exc:
        raise PingError from exc


def _sample(address, origin, location, samples):
    """Ping a server multiple times.

    :param serverstf.cache.Address address: the address of the server to ping.
    :param origin: a two-tuple containing latitude and longitude of the
        'current' position.
    :param target: a two-tuple containing latitude and longitude of the server.
    :param samples int: the number of times to ping the server.

    :return: a generator that will yield up to ``samples`` number of tuples
        containing the distance between the two locations in metres and ping
        in seconds.
    """
    dist = _distance(origin, location)
    for x in range(samples):  # pylint: disable=unused-variable
        try:
            yield dist, _ping(address)
        except PingError:
            pass


def _poll(address, *, cache, origin, samples):
    """Ping a server from the cache.

    This will attempt to ping a server identified an address. It will
    determine location of server by reading it from the cache. If the server
    doesn't exist in the cache or the ``latitude`` or ``longitude`` fields
    are not set then no results will be returned.

    :param serverstf.cache.Address address: the address of the server to ping.
    :param cache: see :func:`_thread_local_cache`.
    :param origin: a two-tuple containing latitude and longitude of the
        'current' position.
    :param samples int: the number of times to ping the server.

    :return: a list of no more than ``sample`` tuples containing the distance
        between the origin and server and the ping.
    """
    results = []
    with cache() as cache_i:
        status = cache_i.get(address)
        if (status.latitude is not None
                and status.longitude is not None):
            results.extend(_sample(
                address,
                origin,
                (status.latitude, status.longitude),
                samples,
            ))
    return results


def _thread_local_cache(local, redis_url):
    """Create thread-local caches.

    :return: a context manager factory that when entered return a
        :class:`serverstf.cache.Cache` that is local to the current thread.
    """

    @contextlib.contextmanager
    def context():  # pylint: disable=missing-docstring
        if not hasattr(local, "cache"):
            local.cache = serverstf.cache.Cache.connect(
                redis_url, asyncio.new_event_loop())
        yield local.cache

    return context


@serverstf.cli.subcommand("latency")
@serverstf.cli.redis
@serverstf.cli.argument("longitude", type=float)
@serverstf.cli.argument("latitude", type=float)
@serverstf.cli.argument(
    "--threads",
    type=int,
    default=multiprocessing.cpu_count(),  # pylint: disable=no-member
    help=("The number of threads to spawn to ping servers. "
          "Defaults to number of CPU cores available."),
)
@serverstf.cli.argument(
    "--samples",
    type=int,
    default=3,
    help="The number of samples to take per server. Default is three.",
)
@serverstf.cli.argument(
    "--output",
    type=pathlib.Path,
    help="The file to write results to.",
    required=True,
)
def _ping_all(args):
    """Ping all servers in the cache."""
    loop = asyncio.get_event_loop()
    with args.output.open("a") as output:
        with serverstf.cache.Cache.connect(args.redis, loop) as i_cache:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=args.threads) as executor:
                poll_bound = functools.partial(
                    _poll,
                    cache=_thread_local_cache(threading.local(), args.redis),
                    origin=(args.latitude, args.longitude),
                    samples=args.samples,
                )
                sample_count = 0
                sample_count_total = 0
                for results in executor.map(
                        poll_bound, i_cache.all_iterator()):
                    for sample in results:
                        sample_count += 1
                        sample_count_total += 1
                        output.write("{0!r},{1!r}\n".format(*sample))
                    if sample_count >= 50:
                        log.info(
                            "Flushing %s results to %s; %s total",
                            sample_count, args.output, sample_count_total)
                        output.flush()
                        sample_count = 0
                output.flush()
                log.info("Collected %s samples", sample_count_total)


def _read_csv(csv_fp):
    """Read latency CSV data.

    This reads a file containing comma-separated latency data as produced by
    :func:`_ping_all`. Each row has two fields: the distance in metres and the
    latency in second; both as floats.

    :param csv_fp: a file-like object open for reading.

    :return: two lists. The former containing the distances and the latter
        the latencies.
    """
    distances = []
    latencies = []
    for line in csv_fp:
        distance, latency = (float(f) for f in line.split(",", 2))
        distances.append(distance)
        latencies.append(latency)
    return distances, latencies


def _linear_regression(distances, latencies):
    """Calculate linear regression for latencies.

    :param distances: list of distances.
    :param latencies: list of latencies corresponding to the given distances.

    :return: a tuple containing the gradient and intercept of the fitted
        linear regression.
    """
    length = len(list(zip(distances, latencies)))
    distances_mean = sum(distances) / len(distances)
    latencies_mean = sum(latencies) / len(latencies)
    numerator = sum(
        (d * l) - (length * distances_mean * latencies_mean)
        for d, l in zip(distances, latencies)
    )
    denominator = sum(
        (d ** 2) - (length * distances_mean ** 2)
        for d in distances
    )
    gradient = numerator / denominator
    intercept = latencies_mean - (gradient * distances_mean)
    return gradient, intercept


@serverstf.cli.subcommand("latency-curve")
@serverstf.cli.argument(
    "data",
    type=pathlib.Path,
    help=("A CSV file containing the distance "
          "and latency data to generate curve for."),
)
@serverstf.cli.argument(
    "--output",
    type=pathlib.Path,
    help="A file to write the curve JSON to.",
)
def _write_curve(args):
    """Write a latency curve JSON file.

    This writes a JSON object to an output file. The object has two fields:
    ``gradient`` and ``intercept`` which is the linear regression of the
    given latency data.
    """
    with args.data.open() as data:
        distances, latencies = _read_csv(data)
        with args.output.open("w") as curve:
            gradient, intercept = _linear_regression(distances, latencies)
            json.dump({
                "gradient": gradient,
                "intercept": intercept,
            }, curve)
    log.info("Latency curve written to %s", args.output)


@serverstf.cli.subcommand("latency-plot")
@serverstf.cli.argument(
    "data",
    type=pathlib.Path,
    help="A CSV file containing the distance and latency data to plot.",
)
def _plot_ping(args):
    """Plot and display latency data in a browser."""
    distances = []
    latencies = []
    with tempfile.NamedTemporaryFile(suffix=".html") as output:
        bokeh.plotting.output_file(output.name, title="Latency Curve")
        with args.data.open() as data:
            distances, latencies = _read_csv(data)
            distances = [d / 1000.0 for d in distances]
            latencies = [l * 1000.0 for l in latencies]
        figure = bokeh.plotting.figure(
            title="Latency Curve",
            x_axis_label="Distance (km)",
            y_axis_label="Latency (ms)",
        )
        figure.scatter(distances, latencies, color="#5b7a8c", marker="x")
        gradient, intercept = _linear_regression(distances, latencies)
        distance_max = max(distances)
        regression_x, regression_y = zip(
            [0, intercept],
            [distance_max, (distance_max * gradient) + intercept],
        )
        figure.line(regression_x, regression_y, color="#9d302f")
    bokeh.plotting.show(figure)
