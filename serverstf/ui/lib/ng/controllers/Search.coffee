define ->

    TAGS = [
        "tf2",
        "gmod",
        "mode:cp",
        "mode:ctf",
        "mode:surf",
        "mode:jump",
        "mode:mvm",
        "population:full",
        "population:empty",
        "population:active",
    ]

    factory = ($scope, $location, Server, Socket) ->

        # Server search controller.
        #
        # This controller maintains a set of tags to search for. Each tag
        # can be in one of three modes: required, excluded or optional.
        # The required and excluded modes are used to filter which servers
        # are shown. Optional tags on the other hand are used purely for
        # influencing the ranking of a server in the results.
        #
        # Note that this controller watches for $locationChangeSuccess
        # events so that it can react to users navigating via the likes of
        # the back button. Because of this it's important that any routing
        # to this controller has *reload on search* disabled.
        class Search

            constructor: ->
                @REQUIRED = "!"
                @OPTIONAL = "~"
                @EXCLUDED = "-"
                @_removeConnectObservation = ->
                @results = []
                @suggestions = []
                @tags = []  # [{mode: ..., tag: ...}, ...]
                $scope.tag = ""
                Socket.on("match", @_onMatch, $scope)
                @tags.push(
                    @_parseTagExpression($location.search().tags or "") ...)
                @_setQuery()
                $scope.$watch("tag", @_updateSuggestions)
                $scope.$on("$locationChangeSuccess", =>
                    @tags.length = 0
                    @tags.push(@_parseTagExpression(
                        $location.search().tags or "") ...)
                    @_setQuery()
                )

            # Handler for `match` socket messages.
            #
            # If the corresponding server is not already in the result list
            # then it will be added.
            _onMatch: ({ip, port}) =>
                server = Server.get(ip, port)
                if server not in @results
                    @results.push(server)
                else
                    server.free()

            # Parse a string containing one or more tags.
            #
            # Tag expressions are comma-separated lists of tags. Each tag
            # is optionally prefixed with a mode identifier: `!`, `-` and `~`
            # for required, excluded and optional modes respectively. If a
            # tag doesn't have a mode identifier then it default to optional.
            #
            # This returns an array of objects. Each object has a `mode` and
            # `tag` field. The `mode` is the mode identifier and `tag` is
            # everything after the identifier; each as a string.
            #
            # The `tag` field will never be empty.
            _parseTagExpression: (expression) =>
                tags = []
                for tag_expression in expression.split(",")
                    if tag_expression.length < 2
                        continue
                    if tag_expression.slice(0, 1) not in
                            [@REQUIRED, @EXCLUDED, @OPTIONAL]
                        tag_expression = "#{@OPTIONAL}#{tag_expression}"
                    tags.push(
                        mode: tag_expression.slice(0, 1)
                        tag: tag_expression.slice(1)
                    )
                return tags

            # Build a tag expression string from the current tags.
            #
            # This is the inverse of `_parseTagExpression` which uses the
            # current `@tags` to build the string.
            #
            # The returned expression string will have the tags sorted
            # lexicographically. Optional tags will not have the `~` mode
            # identifier.
            _generateTagExpression: =>
                tags = []
                for tag in @tags
                    mode = if tag.mode == @OPTIONAL then "" else tag.mode
                    tags.push("#{mode}#{tag.tag}")
                return tags.sort().join(",")

            # Update the current tag suggestions.
            #
            # Given a tag expression this will search through all the known
            # tags and popular `@suggestions` with those which appear to
            # match the expression.
            #
            # The suggestions will be sorted from most to least likely to
            # match.
            #
            # Although any tag expression is valid as the sole argument note
            # that only the first tag in the expression is considered. If the
            # expression contains no tags then the suggestions will be emptied.
            _updateSuggestions: (expression) =>
                suggestions = []  # [[score, tag], ...]
                query = @_parseTagExpression(expression)[0]
                if query
                    for tag in TAGS
                        parts = tag.split(":")
                        safe_query = query.tag.replace(
                            /[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&")
                        regex = new RegExp("#{safe_query}?", "i")
                        score = 0
                        for part, index in parts
                            if regex.test(part)
                                score += 1 + (index / parts.length) \
                                    + (query.tag.length / part.length)
                        if score > 0
                            suggestions.push([score, tag])
                        @suggestions = suggestions
                            .sort(([score, tag]) -> -score)
                            .map(([score, tag]) -> tag)
                else
                    @suggestions.length = 0

            # Filter out servers that do not match the query.
            #
            # This will check every server in the current results set to
            # ensure that they all have the required tags and none of the
            # exlcuded ones. If a server doesn't satify this requirement
            # then it is removed from the results set and freed.
            _filter: =>
                include = []
                exclude = []
                for {mode, tag} in @tags
                    if mode == @REQUIRED
                        include.push(tag)
                    else if mode == @EXCLUDED
                        exclude.push(tag)
                @results = @results.filter((server) ->
                    for tag in server.tags
                        if tag in exclude
                            return false
                    for include_tag in include
                        if include_tag not in server.tags
                            return false
                    return true
                )

            # Set current query on the socket.
            #
            # This sends a `query` message to the socket with the current
            # required and excluded tags set. Once the query is set all
            # future received `match` messages will conform to the required
            # and excluded tags.
            #
            # The existing resutls set will be filtered to exclude servers
            # that do not match the new query.
            _setQuery: =>
                include = []
                exclude = []
                for {mode, tag} in @tags
                    if mode == @REQUIRED
                        include.push(tag)
                    else if mode == @EXCLUDED
                        exclude.push(tag)
                @_removeConnectObservation()
                @_removeConnectObservation = Socket.observeConnect(->
                    Socket.send("query", {include: include, exclude: exclude})
                , $scope)
                @_filter()
                # TODO: Work out how this doesn't cause the
                #       $locationChangeSuccess handler to enter
                #       an infinite loop.
                $location.search(tags: @_generateTagExpression())

            # Add a tag to the list of tags to search.
            #
            # This will add the given tag to the list of tags currently
            # applied to the search, resetting the query on the server as
            # necessary.
            #
            # The scope field `tag` is parsed as a tag expression in order to
            # determine the tag mode. Note that only the first tag in the
            # expression is used.
            #
            # Additionally, if the `tag` argument is not provided then the
            # tag name from the tag expression is used.
            #
            # If the tag already exists within the search tags with the same
            # tag mode then this does nothing. If the mode is different
            # however then it will be updated to the new value and the query
            # will be set.
            submit: (tag) =>
                query = @_parseTagExpression($scope.tag)[0]
                if not query
                    return
                if not tag
                    tag = query.tag
                for existing_tag in @tags
                    if existing_tag.tag == tag
                        if existing_tag.mode != query.mode
                            existing_tag.mode = query.mode
                            @_setQuery()
                            return
                        else
                            return
                @tags.push(mode: query.mode, tag: tag)
                @_setQuery()

            # Remove a tag from the list of search tags by value.
            removeTag: (remove) =>
                index = @tags.indexOf(remove)
                if index >= 0
                    @tags.splice(index, 1)
                    @_setQuery()

            # Generate a rank score for a server.
            #
            # This method is designed for use with the likes of the `orderBy`
            # filter. It returns a numeric score which ranks servers with the
            # most matching optional tags and highest population last.
            rank: (server) =>
                score = 0
                optional_tags = []
                for {mode, tag} in @tags
                    if mode == @OPTIONAL
                        optional_tags.push(tag)
                for tag in optional_tags
                    if tag in server.tags
                        score += 1
                score += server.players.current / server.players.max
                return score

        return new Search()

    return _ =
        "name": "Search"
        "dependencies": ["$scope", "$location", "Server", "Socket"]
        "controller": factory
