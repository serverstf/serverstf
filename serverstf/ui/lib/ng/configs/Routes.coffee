define ["angular-route"], (angular_route) ->

    ROUTES =
        "/search/": "templates/search.html"
        "/statistics/": "templates/placeholder.html"
        "/favourites/": "templates/placeholder.html"

    configureRoutes = ($locationProvider, $routeProvider) ->
        $locationProvider.html5Mode(true)
        for pattern, template of ROUTES
            console.log("Add route #{pattern} <- #{template}")
            $routeProvider.when(pattern, {templateUrl: template})

    return _ =
        "name": "Routes"
        "dependencies": ["$locationProvider", "$routeProvider"]
        "modules": ["ngRoute"]
        "config": configureRoutes
