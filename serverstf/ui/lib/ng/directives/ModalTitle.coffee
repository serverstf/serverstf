define ->

    factory = () ->

        link = (scope, element, attrs, controller) ->
            scope.$watch("svtfModalTitle", (title) ->
                controller.title = title
            )

        return _ =
            restrict: "A"
            require: "^svtfModal"
            scope:
                svtfModalTitle: "="
            link: link

    return _ =
        "name": "svtfModalTitle"
        "dependencies": []
        "directive": factory
