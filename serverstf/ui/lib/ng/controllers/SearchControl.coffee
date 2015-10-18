define ->

    factory = ($scope, Server, Socket) ->

        class SearchControl
            constructor: ->
                @INCLUDE = "+"
                @EXCLUDE = "-"
                @OPTIONAL = ""
                @query = []
                $scope.tag = ""
                Socket.onScoped($scope, "tag_add", @_onTagAdd)
                Socket.onScoped($scope, "tag_remove", @_onTagAdd)
                @addTag("tf2", @INCLUDE)
                @servers = [
                    Server.get("198.24.175.75", 27015),
                ]
                console.log(Server._servers)

            submit: ->
                if $scope.tag
                    @addTag($scope.tag, @INCLUDE)
                $scope.tag = ""

            addTag: (tag, mode) ->
                @query.push(
                    tag: tag
                    mode: mode
                )
                Socket.send("subscribe_tag", tag)

        return new SearchControl()

    return _ =
        "name": "SearchControl"
        "dependencies": ["$scope", "Server", "Socket"]
        "controller": factory
