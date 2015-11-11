define ->

    factory = (Location, Modal) ->

        class SettingsLocation

            constructor: ->
                Modal.title = "Settings"
                @coordinates = Location.coordinates

        return new SettingsLocation()


    return _ =
        name: "SettingsLocation"
        dependencies: ["Location", "Modal"]
        controller: factory
