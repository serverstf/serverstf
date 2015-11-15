define ->

    factory = ->
        return (server) ->
            return "steam://connect/#{server.ip}:#{server.port}"

    return _ =
        name: "connect"
        filter: factory
