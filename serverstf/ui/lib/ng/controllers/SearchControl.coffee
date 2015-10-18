define ->

    factory = ($scope, Socket) ->

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
        "dependencies": ["$scope", "Socket"]
        "controller": factory
