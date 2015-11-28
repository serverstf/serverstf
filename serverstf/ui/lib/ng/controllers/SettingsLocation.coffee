define ->

    factory = (Config, Location) ->

        class SettingsLocation

            constructor: ->
                @coordinates = Location.coordinates
                Config.observe(
                    "geolocation:enabled",
                    Config.TYPES.BOOLEAN,
                    false,
                    (value) =>
                        console.log(typeof value, value)
                        @geolocation = value
                )

        return new SettingsLocation()


    return _ =
        name: "SettingsLocation"
        dependencies: ["Config", "Location"]
        controller: factory
