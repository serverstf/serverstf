define ["angular-ui-router"], (angular_ui_route) ->

    STATES =
        home:
            url: "/"
            views:
                primary:
                    templateUrl: "templates/placeholder.html"
        search:
            url: "/search/?tags"
            reloadOnSearch: false
            views:
                primary:
                    templateUrl: "templates/search.html"
        statistics:
            url: "/statistics/"
            views:
                primary:
                    templateUrl: "templates/placeholder.html"
        favourites:
            url: "/favourites/"
            views:
                primary:
                    templateUrl: "templates/placeholder.html"

    configureStates = ($locationProvider, $stateProvider) ->
        $locationProvider.html5Mode(true)
        for state, configuration of STATES
            $stateProvider.state(state, configuration)

    return _ =
        "name": "States"
        "dependencies": ["$locationProvider", "$stateProvider"]
        "modules": ["ui.router"]
        "config": configureStates
