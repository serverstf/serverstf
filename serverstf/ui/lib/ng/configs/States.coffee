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
                    templateUrl: "templates/settings/settings.html"
                    controller: ["$state", ($state) ->
                        if $state.current.name == "modal.settings"
                            $state.go('.search')
                    ]
        "modal.settings.search":
            url: "search/"
            views:
                "settings":
                    templateUrl: "templates/settings/search.html"
        "modal.settings.location":
            url: "location/"
            views:
                "settings":
                    templateUrl: "templates/settings/location.html"
        "modal.settings.licenses":
            url: "licenses/"
            views:
                "settings":
                    templateUrl: "templates/settings/licenses.html"
        "modal.sign-in":
            url: "/sign-in/"
            views:
                "modal@":
                    templateUrl: "templates/dialogues/sign-in.html"
        "modal.server":
            url: "/servers/{address}/"
            views:
                "modal@":
                    templateUrl: "templates/dialogues/server-details.html"

    configureStates = ($locationProvider, $stateProvider) ->
        $locationProvider.html5Mode(true)
        for state, configuration of STATES
            $stateProvider.state(state, configuration)

    return _ =
        "name": "States"
        "dependencies": ["$locationProvider", "$stateProvider"]
        "modules": ["ui.router", "ct.ui.router.extras"]
        "config": configureStates
