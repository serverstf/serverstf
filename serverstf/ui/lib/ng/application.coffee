define ["angular"], (angular) ->
    # The Angular application specification describes the make up of the
    # Angular application that will be loaded by `initialise`. Specifically
    # NG_APPLICATION_SPECIFICATION is a object which maps Angular service/
    # types (e.g. controller, service, etc.) to AMD modules. See `initialise`
    # for further details.
    NG_APPLICATION_MODULE_NAME = "serverstf"
    NG_APPLICATION_SPECIFICATION =
        "controller": [
            "SearchControl",
        ]
        "directive": [
            "Modal",
        ]
        "service": [
            "Server",
            "Socket",
        ]

    # Bootstrap the Angular application.
    #
    # This creates an Angular modules and adds all the services given to it
    # before finally bootstrapping the document with the newly created module.
    #
    # @param modules [Array] A list of objects describing Angular services.
    bootstrap = (modules) ->
        ng_module_dependencies = []
        for module in modules
            for ng_module_dependency in module.modules or []
                if ng_module_dependency not in ng_module_dependencies
                    ng_module_dependencies.push(ng_module_dependency)
        console.log("Application module #{NG_APPLICATION_MODULE_NAME}
                    <- #{ng_module_dependencies}")
        ng_module = angular.module(
            NG_APPLICATION_MODULE_NAME, ng_module_dependencies)
        for module in modules
            ng_dependencies = module.dependencies or []
            console.log("Add #{module.type} '#{module.name}' <-
                        #{ng_dependencies} from #{module.path}")
            service = module[module.type]
            if not service
                console.warn(
                    "Module #{module.path} doesn't define a #{module.type}")
            ng_module[module.type](
                module.name, ng_dependencies.concat(service))
        angular.bootstrap(document, [NG_APPLICATION_MODULE_NAME])

    # Initialise the Angular application.
    #
    # This inspects the `NG_APPLICATION_SPECIFICATION` in order to determine
    # which modules to load. Each Angular service/specialised object should
    # live in its own AMD module in a file in a subdirectory of this, the
    # `ng/` directory which is named to correspond to the service type.
    # For example, if the module exposes an Angular controller it goes in
    # `ng/controllers/` -- note the pluralisation.
    #
    # Every module in the application is loaded via calls to `require`.
    # Each module is expected to expose a number of keys:
    #
    # * `name` -- the name of the Angular service.
    # * `modules` -- an optional array of Angular modules the service depends
    #       on.
    # * `dependencies` -- an optional array of other Angular services the
    #       new service depends on.
    #
    # The service implementation should be keyed against the type of service.
    # So, if it's a controller it would be: `controller: MyController`.
    #
    # As well as this the exported module object is extended to have a `path`
    # and `type` fields. The former is the path used to `require` the module
    # and `type` is the type of Angular service.
    #
    # Once all modules have been loaded `bootstrap` is called which will
    # actually bootstrap the Angular application.
    initialise = ->
        start = Date.now()
        modules = []
        outstanding = 0
        for type, modules_names of NG_APPLICATION_SPECIFICATION
            for module_name in modules_names
                outstanding += 1
                module_path = "ng/#{type}s/#{module_name}"
                require([module_path], ((type, path, module) ->
                    module.path = path
                    module.type = type
                    modules.push(module)
                    outstanding -= 1
                    if outstanding == 0
                        bootstrap(modules)
                        console.info("Application initialisation
                                     took #{Date.now() - start}ms")
                ).bind(this, type, module_path))

    return _ =
        "initialise": initialise
