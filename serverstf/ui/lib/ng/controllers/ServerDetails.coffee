define ->

    factory = ->

        class ServerDetails

            constructor: ->
                @foo = "bar"

        return new ServerDetails()

    return _ =
        "name": "ServerDetails"
        "dependencies": []
        "controller": factory
