define ->

    factory = ($scope, Modal, Server) ->

        class ServerDetails

            constructor: ->
                config = Modal.getConfig()
                @server = Server.get(config.ip, config.port)
                $scope.$watch(
                    => @server.name
                    (name) -> Modal.title = name
                )

        return new ServerDetails()

    return _ =
        "name": "ServerDetails"
        "dependencies": ["$scope", "Modal", "Server"]
        "controller": factory
