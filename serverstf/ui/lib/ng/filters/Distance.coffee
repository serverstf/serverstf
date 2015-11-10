# Determine distance between user and server in metres.
#
# This filter calculates the distance between the user's current location
# and the location of a server in metres.
#
# The filter accepts an additional scale factor argument which is the power
# of 10 to scale the latency value by. For example, 3 would be kilometres.

define ->
    USER_LATITUDE = 52.135973
    USER_LONGITUDE = -0.466655

    radians = (degrees) ->
        return degrees * (Math.PI / 180.0)

    factory = (Location) ->
        EARTH_RADIUS = 6371000  # metres
        return (server, scale_factor) ->
            u_latitude = radians(Location.coordinates.latitude)
            u_longitude = radians(Location.coordinates.longitude)
            s_latitude = radians(server.latitude)
            s_longitude = radians(server.longitude)
            scale = Math.pow(10, scale_factor or 0)
            return 2 * EARTH_RADIUS * Math.asin(
                Math.pow(Math.sin((u_latitude - s_latitude) / 2), 2) +
                Math.cos(s_latitude) *
                Math.cos(u_latitude) *
                Math.pow(Math.sin((u_longitude - s_longitude) / 2), 2)
            ) / scale

    return _ =
        "name": "distance"
        "dependencies": ["Location"]
        "filter": factory
