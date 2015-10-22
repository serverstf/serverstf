define ->

    factory = ($compile, Modal) ->

        link = (scope, element) ->
            console.log(scope, element)
            scope.$watch(
                -> Modal.getDialogue()
                ([controller, template]) ->
                    element.empty()
                    if controller and template
                        attrs =
                            "src": "'#{template}'"
                            "ng-controller": controller
                        include = angular.element("<ng-include></ng-include>")
                        include.attr("src", "'#{template}'")
                        include.attr("ng-controller",
                                     "#{controller} as controller")
                        $compile(include)(scope)
                        element.append(include)
                true
            )


        return _ =
            restrict: "E"
            link: link

    return _ =
        "name": "svtfModalContent"
        "dependencies": ["$compile", "Modal"]
        "directive": factory
