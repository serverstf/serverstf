define ->

    factory = ($parse, $rootScope, Modal) ->

        link = (scope, element, attributes) ->
            element.on("click", ->
                $rootScope.$applyAsync(->
                    controller = null
                    configuration = $parse(attributes.svtfModalOpen)(scope)
                    if typeof configuration == "string"
                        controller = configuration
                        configuration = {}
                    else
                        controller = configuration[0]
                        configuration = configuration[1]
                    Modal.open(controller, configuration)
                )
            )

        return _ =
            restrict: "A"
            link: link

    return _ =
        "name": "svtfModalOpen"
        "dependencies": ["$parse", "$rootScope", "Modal"]
        "directive": factory
