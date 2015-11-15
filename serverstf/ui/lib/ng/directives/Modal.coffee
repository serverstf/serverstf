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
        element.on("click", (event) ->
            scope.$applyAsync(->
                if event.target == element[0]
                    controller.close()
            )
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
