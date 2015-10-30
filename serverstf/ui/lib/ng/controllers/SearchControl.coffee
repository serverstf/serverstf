define ->

    factory = ($scope, Server, Socket) ->

        # Server search controller.
        #
        # This controller maintains a set of tags to search for. Each tag
        # can be in one of three modes: required, excluded or optional.
        # The required and excluded modes are used to filter which servers
        # are shown. Optional tags on the other hand are used purely for
        # influencing the ranking of a server in the results.
        class SearchControl

            constructor: ->
                @REQUIRED = "+"
                @EXCLUDE = "-"
                @OPTIONAL = ""
                @query = []
                @servers = []
                $scope.tag = ""
                Socket.on("match", @_onMatch, $scope)
                @_removeConnectObservation = ->
                @addTag("mode:payload", @REQUIRED)

            # Handler for `match` socket messages.
            #
            # If the corresponding server is not already in the result list
            # then it will be added.
            _onMatch: ({ip, port}) =>
                console.log("Match", ip, port)
                server = Server.get(ip, port)
                if server not in @servers
                    @servers.push(server)
                else
                    server.free()

            # Filter the current result set by the query.
            #
            # This removes any servers in the results list that no longer
            # have all the required tags and none of the excluded tags.
            # If a server is removed from the list then it will be freed.
            _filter: ->
                @servers = @servers.filter((server) =>
                    for {mode, tag} in @query
                        if ((mode == @REQUIRED and tag not in server.tags) \
                                or (mode == @EXCLUDE and tag in server.tags))
                            server.free()
                            return false
                    return true
                )

            # Set current query on the socket.
            #
            # This sends a `query` message to the socket with the current
            # required and excluded tags set. Once the query is set all
            # future received `match` messages will conform to the required
            # and excluded tags.
            _setQuery: ->
                include = []
                exclude = []
                for {mode, tag} in @query
                    if mode == @REQUIRED
                        include.push(tag)
                    else if mode == @EXCLUDE
                        exclude.push(tag)
                @_removeConnectObservation()
                @_removeConnectObservation = Socket.observeConnect(->
                    Socket.send("query", {include: include, exclude: exclude})
                , $scope)

            submit: ->
                if $scope.tag
                    @addTag($scope.tag, @REQUIRED)
                $scope.tag = ""

            # Add a tag to the current query.
            #
            # This will filter the current result set as necessary and set
            # socket query.
            addTag: (tag, mode) ->
                @query.push(
                    tag: tag
                    mode: mode
                )
                @_filter()
                @_setQuery()

        return new SearchControl()

    return _ =
        "name": "SearchControl"
        "dependencies": ["$scope", "Server", "Socket"]
        "controller": factory
