define ->

    factory = (Config, Location, Modal) ->

        class SettingsLocation

            constructor: ->
                Modal.title = "Settings"
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
        dependencies: ["Config", "Location", "Modal"]
        controller: factory
