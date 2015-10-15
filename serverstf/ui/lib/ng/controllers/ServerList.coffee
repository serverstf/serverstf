define ->

    class ServerList

        constructor: (Socket) ->
            @address =
                ip: "0.0.0.0"
                port: 9001

    return _ =
        "name": "ServerList"
        "dependencies": ["Socket"]
        "controller": ServerList
