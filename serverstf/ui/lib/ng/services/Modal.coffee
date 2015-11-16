define ->

    DIALOGUES =
        "ServerDetails": "templates/dialogues/server-details.html"
        "SignIn": "templates/dialogues/sign-in.html"
        "SettingsLocation": "templates/settings/location.html"

    factory = ->

        class Modal

            constructor: ->
                @_is_open = false
                @_dialogue =
                    controller: null
                    template: null
                @_configuration = {}
                @title = ""

            getDialogue: =>
                return [@_dialogue.controller, @_dialogue.template]

            getConfig: =>
                return @_configuration

            isOpen: =>
                return @_is_open

            open: (controller, configuration) =>
                if controller not of DIALOGUES
                    console.error("No template for #{controller} dialogue")
                    return
                @_configuration = configuration
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
