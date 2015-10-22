define ->

    DIALOGUES =
        "ServerDetails": "templates/dialogues/server-details.html"

    factory = ->

        class Modal

            constructor: ->
                @_is_open = false
                @_dialogue =
                    controller: null
                    template: null
                @title = ""

            getDialogue: =>
                return [@_dialogue.controller, @_dialogue.template]

            isOpen: =>
                return @_is_open

            open: (controller, configuration) =>
                if controller not of DIALOGUES
                    console.error("No template for #{controller} dialogue")
                    return
                @_dialogue =
                    controller: controller
                    template: DIALOGUES[controller]
                @_is_open = true

            close: =>
                @_is_open = false
                @_dialogue =
                    controller: null
                    template: null

        return new Modal()

    return _ =
        "name": "Modal"
        "dependencies": []
        "service": factory
