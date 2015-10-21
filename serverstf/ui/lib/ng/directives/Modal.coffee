define ->

    link = (scope, element, attrs, controller) ->
        scope.$watch(
            -> controller.isOpen(),
            (open) ->
                if open
                    element.addClass("svtf-modal-open")
                else
                    element.removeClass("svtf-modal-open")
        )

    factory = ->
        return _ =
            restrict: "E"
            templateUrl: "templates/modal.html"
            controller: ["Modal", (Modal) -> Modal]
            controllerAs: "modal"
            link: link

    return _ =
        "name": "svtfModal"
        "dependencies": []
        "directive": factory
