define ->

    factory = (User) ->

        class Header

            constructor: ->
                @user = User

        return new Header()

    return _ =
        name: "Header"
        dependencies: ["User"]
        controller: factory
