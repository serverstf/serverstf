define ->

    factory = ($scope, Modal, Server) ->

        class ServerDetails

            constructor: ->
                config = Modal.getConfig()
                @server = Server.get(config.ip, config.port)
                @players = []
                $scope.$watch(
                    => @server.name
                    (name) -> Modal.title = name
                )
                $scope.$watch(
                    => @server.players,
                    @_updatePlayers
                )

            _updatePlayers: (players) =>
                @players.length = 0
                for [name, score, duration] in players.scores
                    @players.push(
                        name: name,
                        score: score,
                        duration: duration,
                        rate: score / (duration / 60),
                    )

        return new ServerDetails()

    return _ =
        "name": "ServerDetails"
        "dependencies": ["$scope", "Modal", "Server"]
        "controller": factory
