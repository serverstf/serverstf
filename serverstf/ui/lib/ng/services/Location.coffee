define ->

    factory = ($http, $rootScope, $window) ->

        # Access the user's location.
        #
        # This service provides mechanisms to access the user's latitude
        # and longitude coordinates. Primarily these are exposed as the
        # `coordinates` property or by registering an observer.
        #
        # The service will try to use multiple sources to determine the
        # user's position. If enabled and available, the browser's own
        # geolocation API. As a fallback the `services/location` backend
        # endpoint is used which performs a GeoIP lookup for the sending
        # client's IP but this can be inaccurate.
        #
        # Which source is being used is indicated by the `source` property
        # which will be one of the constants from `SOURCES` object.
        class Location

            constructor: ->
                @SOURCES = {}
                for source in ["default", "ip", "geolocation"]
                    @SOURCES[source.toUpperCase()] = source
                @source = @SOURCES.DEFAULT
                @geolocation =
                    available: $window.navigator.geolocation != undefined
                    enabled: true
                    blocked: false
                @coordinates =
                    latitude: 0,
                    longitude: 0,
                @_observers = []
                $http.get("services/location").then(({data}) =>
                    @_setCoordinates(
                        data.latitude, data.longitude, @SOURCES.IP)
                ).finally(@_watchGeolocation)

            # Set the location coordinates.
            #
            # This updates the coordinates and the source to the given values
            # then invokes all of the observers before finally performing a
            # scope digest.
            _setCoordinates: (latitude, longitude, source) =>
                @source = source
                @coordinates.latitude = latitude
                @coordinates.longitude = longitude
                $rootScope.$applyAsync(=>
                    for observer in @_observers
                        observer(@coordinates)
                )

            # Watch for position changes using geolocation.
            #
            # If the user has blocked geolocation in their browser then
            # the `geolocation.blocked` property will be set to `true`.
            #
            # If geolocation is not available or not enabled then this
            # method does nothing.
            _watchGeolocation: =>
                if not @geolocation.enabled or not @geolocation.available
                    return
                $window.navigator.geolocation.watchPosition(
                    (position) =>
                        @_setCoordinates(
                            position.coords.latitude,
                            position.coords.longitude,
                            @SOURCES.GEOLOCATION,
                        )
                    (error) =>
                        if error.code == error.PERMISSION_DENIED
                            @geolocation.blocked = true
                )

            # Observe coordinate changes.
            #
            # This registers a function that will be called whenever the
            # known coordinates of the user changes. When an observer is
            # called it is pased the `coordinates` object.
            #
            # When an observer is first registered it is called immediately
            # with current coordinates being passed in.
            #
            # Returns a function which can be used to unregister the
            # observer.
            observe: (observer) =>
                removeObserver = =>
                    index = @_observers.indexOf(observer)
                    if index >= 0
                        @_observers[observer].splice(index, 1)

                observer(@coordinates)
                return removeObserver

        return new Location()

    return _ =
        "name": "Location"
        "dependencies": ["$http", "$rootScope", "$window"]
        "service": factory
