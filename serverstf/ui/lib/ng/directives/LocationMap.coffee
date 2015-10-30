define ["d3", "topojson"], (d3, topojson) ->

    factory = ($http) ->
        bindProjectionToScope = (scope, projection) ->
            centreProjection = ->
                projection.center([scope.longitude, scope.latitude])
            centreProjection()
            scope.$watch("latitude", centreProjection)
            scope.$watch("longitude", centreProjection)

        link = (scope, element) ->
            svgFromTopoJSON = ({data}) ->
                projection = d3.geo.mercator().scale(250)
                path = d3.geo.path().projection(projection)
                svg = d3.select(element[0]).append("svg")
                features = topojson.feature(
                    data, data.objects.countries).features
                svg.selectAll("path")
                    .data(features)
                    .enter()
                    .append("path")
                    .attr("d", path)
                bindProjectionToScope(scope, projection)

            $http.get(
                "data/world-50m.json", {cache: true}).then(svgFromTopoJSON)

        return _ =
            restrict: "E"
            scope:
                longitude: "="
                latitude: "="
            link: link

    return _ =
        "name": "svtfLocationMap"
        "dependencies": ["$http"]
        "directive": factory
