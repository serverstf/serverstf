define ->

    controller = ($state, $stickyState) ->

        class Modal

            constructor: ->
                @title = ""

            close: ->
                states = $stickyState.getInactiveStates()
                if states.length
                    for state in states
                        if "primary@" of state.views
                            $state.go(state.name)
                else
                    $state.go("home")

        return new Modal()

    factory = ($state) ->

        link = (scope, element, attrs, controller) ->
            scope.$watch(
                -> $state.includes("modal")
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

        return _ =
            restrict: "E"
            templateUrl: "templates/modal.html"
            controller: ["$state", "$stickyState", controller]
            controllerAs: "modal"
            link: link

    return _ =
        "name": "svtfModal"
        "dependencies": ["$state"]
        "directive": factory
