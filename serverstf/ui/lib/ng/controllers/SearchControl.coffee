define ->

    factory = ($scope, Socket) ->

        class SearchControl
            constructor: ->
                @INCLUDE = "+"
                @EXCLUDE = "-"
                @OPTIONAL = ""
                @query = []
                $scope.tag = ""

            submit: ->
                if $scope.tag
                    @addTag($scope.tag, @INCLUDE)
                $scope.tag = ""

            addTag: (tag, mode) ->
                @query.push(
                    tag: tag
                    mode: mode
                )

        return new SearchControl()

    return _ =
        "name": "SearchControl"
        "dependencies": ["$scope", "Socket"]
        "controller": factory
