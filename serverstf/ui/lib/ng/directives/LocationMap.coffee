define ["d3", "topojson"], (d3, topojson) ->

    TOPOLOGY = null

    factory = ($http) ->

        link = (scope, element) ->
            svg = d3.select(element[0]).append("svg")
            svg.attr("class", "svtf-location-map-canvas")

            addTopology = ({data}) ->
                if not TOPOLOGY
                    land = topojson.feature(data, data.objects.land)
                    projection = d3.geo.mercator()
                        .translate([0, 0])
                        .scale(1)
                    path = d3.geo.path().projection(projection)
                    [[left, top], [right, bottom]] = path.bounds(land)
                    TOPOLOGY =
                        topology: land
                        width: right - left
                        height: bottom - top
                scope.$watchGroup(["latitude", "longitude"],
                    ([latitude, longitude]) ->
                        updatePath(TOPOLOGY)
                )

            last_center = []
            updatePath = (topology) ->
                canvas_width = element[0].offsetWidth
                canvas_height = element[0].offsetHeight
                scale_horizontal = topology.width / canvas_width
                scale_vertical = topology.height / canvas_height
                scale = 1 / Math.min(scale_horizontal, scale_vertical)
                coordinates = [scope.longitude, scope.latitude]
                if last_center[0] != coordinates[0] and
                        last_center[1] != coordinates[1]
                    force_redraw = true
                else
                    force_redraw = false
                projection = d3.geo.mercator()
                    .center(coordinates)
                    .translate([canvas_width / 2, canvas_height / 2])
                    .scale(scale * 2)
                path = d3.geo.path().projection(projection)
                drawPath(topology.topology, path, force_redraw)
                last_center = coordinates

            drawPath = (topology, path, redraw) ->
                for class_ in ["land-shadow", "land"]
                    class_full = "svtf-location-map-#{class_}"
                    if redraw
                        svg.selectAll("path.#{class_full}").remove()
                    svg.selectAll("path.#{class_full}")
                        .data([topology])
                        .enter()
                            .append("path")
                            .attr("class", class_full)
                            .attr("d", path)

            $http.get(
                "data/world-50m.json", {cache: true}).then(addTopology)

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
