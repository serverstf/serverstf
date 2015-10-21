define ->

    factory = ->

        class Modal

            constructor: ->
                @_is_open = false
                @title = ""

            isOpen: =>
                return @_is_open

            open: =>
                @_is_open = true

            close: =>
                @_is_open = false

        return new Modal()

    return _ =
        "name": "Modal"
        "dependencies": []
        "service": factory
