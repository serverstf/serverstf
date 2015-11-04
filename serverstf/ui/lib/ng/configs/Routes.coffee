define ["angular-route"], (angular_route) ->

    ROUTES =
        "/": "templates/search.html"

    configureRoutes = ($routeProvider) ->
        for pattern, template of ROUTES
            console.log("Add route #{pattern} <- #{template}")
            $routeProvider.when(pattern, {templateUrl: template})

    return _ =
        "name": "Routes"
        "dependencies": ["$routeProvider"]
        "modules": ["ngRoute"]
        "config": configureRoutes
