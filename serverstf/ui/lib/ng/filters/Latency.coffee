# Get approximate latency between user and server.
#
# This filter loads the latency curve JSON data file and uses it to
# calculate approximate latency based on the distance between the
# user and the server location.
#
# Because the latency curve is loaded asynchronously it is possible,
# for a short time, that the filter would be unable to return the latency.
# In such cases a default value of zero is returned. The default can be
# customised by the second filter argument.
#
# The third filter argument is the scale factor. It is the power of 10 to
# scale the latency value by. By default the scale factor is zero and the
# returned latency is in seconds. If, for example, -3 were used as the
# scale factor then the latency would be in milliseconds.

define ->

    factory = ($filter, $http) ->
        GRADIENT = null
        INTERCEPT = null

        $http.get("data/latency-curve.json").then(({data}) ->
            GRADIENT = data.gradient
            INTERCEPT = data.intercept
        )

        return (server, default_, scale_factor) ->
            if server.hasLocation() and GRADIENT != null and INTERCEPT != null
                latency = GRADIENT * $filter("distance")(server) + INTERCEPT
                latency_clamp = Math.max(0.005, latency)
                scale = Math.pow(10, scale_factor or 0)
                return latency_clamp / scale
            else
                return default_ or 0

    return _ =
        "name": "latency"
        "dependencies": ["$filter", "$http"]
        "filter": factory
