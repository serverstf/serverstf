define ->

    factory = ->
        return _ =
            restrict: "E"
            templateUrl: "templates/modal.html"

    return _ =
        "name": "svtfModal"
        "dependencies": []
        "directive": factory
