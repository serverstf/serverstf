define ->

    factory = ($scope, $http, Modal, Server) ->

        class ServerDetails

            constructor: ->
                config = Modal.getConfig()
                @server = Server.get(config.ip, config.port)
                @players = []
                @players_sort = "-score"
                @map_creators = []
                $scope.$watch(
                    => @server.name
                    (name) -> Modal.title = name
                )
                $scope.$watch(
                    => @server.players,
                    @_updatePlayers
                )
                $scope.$watch(
                    => @server.map
                    @_getMapCreators,
                )

            sortPlayers: (field) =>
                if @players_sort == field
                    @players_sort = "-#{field}"
                else
                    @players_sort = field

            _updatePlayers: (players) =>
                @players.length = 0
                for [name, score, duration] in players.scores
                    @players.push(
                        name: name,
                        score: score,
                        duration: duration,
                        rate: score / (duration / 60),
                    )

            _getMapCreators: =>
                $http.get("data/maps.json", {cache: true}).then(({data}) =>
                    maps = data[@server.application_id]
                    if maps and @server.map of maps
                        @map_creators = maps[@server.map].creators
                        if @map_creators.length > 3
                            @map_creators = [
                                name: "Multiple creators",
                                link: null,
                            ]
                )

        return new ServerDetails()

    return _ =
        "name": "ServerDetails"
        "dependencies": ["$scope", "$http", "Modal", "Server"]
        "controller": factory
