define ->

    factory = ($rootScope, Modal) ->

        link = (scope, element) ->
            element.on("click", ->
                $rootScope.$applyAsync(->
                    Modal.open()
                )
            )

        return _ =
            restrict: "A"
            link: link

    return _ =
        "name": "svtfModalOpen"
        "dependencies": ["$rootScope", "Modal"]
        "directive": factory
