define ->
    CLASS_PREFIX = "svtf-map-x"

    factory = ->

        link = (scope, element) ->
            setMapClasses = (map) ->
                for class_ in element[0].classList
                    if not class_
                        continue
                    if class_.slice(0, CLASS_PREFIX.length) == CLASS_PREFIX
                        element.removeClass(class_)
                if map
                    parts = [CLASS_PREFIX, scope.svtfMap.application_id]
                    parts.push(map.split("_") ...)
                    for _, index in parts
                        class_name = parts.slice(0, index + 1).join("-")
                        element.addClass(class_name)

            scope.$watch("svtfMap.map", setMapClasses)

        return _ =
            restrict: "A"
            scope:
                svtfMap: "="
            link: link

    return _ =
        "name": "svtfMap"
        "dependencies": []
        "directive": factory
