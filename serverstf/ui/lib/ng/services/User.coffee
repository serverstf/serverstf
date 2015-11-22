define ->

    factory = ($document, $http) ->

        class User

            constructor: ->
                @_observers = []
                @profile =
                    id: 0
                    display_name: ""
                    avatar: ""
                @authenticated = false
                $document[0].addEventListener("visibilitychange", @_poll)
                @_poll()

            _poll: =>
                $http.get("services/profile")
                    .then(({data}) =>
                        @authenticated = true
                        @profile.id = data.id
                        @profile.display_name = data.id.toString()
                    )
                    .catch((response) =>
                        if response.status == 403
                            @authenticated = false
                            @profile.id = 0
                            @profile.display_name = ""
                            @profile.avatar = ""
                    )

            signOut: =>
                null

            observe: (observer) =>
                null

        return new User()

    return _ =
        name: "User"
        dependencies: ["$document", "$http"]
        service: factory
