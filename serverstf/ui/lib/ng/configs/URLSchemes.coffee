define ->

    configureURLSchemes = ($compileProvider) ->
        $compileProvider.aHrefSanitizationWhitelist(/(https?|steam):/)
        $compileProvider.imgSrcSanitizationWhitelist(/https?:/)

    return _ =
        name: "URLSchemes"
        dependencies: ["$compileProvider"]
        config: configureURLSchemes
