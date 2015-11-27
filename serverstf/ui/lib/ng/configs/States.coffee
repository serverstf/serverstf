define ["angular-ui-router", "ui-router-extras"], ->

    STATES =
        "home":
            url: "/"
            sticky: true
            views:
                "primary":
                    templateUrl: "templates/placeholder.html"
        "search":
            url: "/search/?tags"
            sticky: true
            reloadOnSearch: false
            views:
                "primary":
                    templateUrl: "templates/search.html"
        "statistics":
            url: "/statistics/"
            sticky: true
            views:
                "primary":
                    templateUrl: "templates/placeholder.html"
        "favourites":
            url: "/favourites/"
            sticky: true
            views:
                "primary":
                    templateUrl: "templates/placeholder.html"
        "modal": {}
        "modal.settings":
            url: "/settings/"
            views:
                "modal@":
                    templateUrl: "templates/settings/location.html"
        "modal.sign-in":
            url: "/sign-in/"
            views:
                "modal@":
                    templateUrl: "templates/dialogues/sign-in.html"

    configureStates = ($locationProvider, $stateProvider) ->
        $locationProvider.html5Mode(true)
        for state, configuration of STATES
            $stateProvider.state(state, configuration)

    return _ =
        "name": "States"
        "dependencies": ["$locationProvider", "$stateProvider"]
        "modules": ["ui.router", "ct.ui.router.extras"]
        "config": configureStates
