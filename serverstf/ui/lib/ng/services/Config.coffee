define ->

    factory = ($http, $window) ->

        NAMESPACE = "configuration:"

        class Config

            constructor: ->
                @TYPES = {}
                for type in ["string", "number", "boolean"]
                    @TYPES[type.toUpperCase()] = type.toUpperCase()
                @_values = {}
                @_observers = {}  # key : [observer, ...]
                @_synchronised = false
                for storage_key, storage_value of $window.localStorage
                    if storage_key.slice(0, NAMESPACE.length) == NAMESPACE
                        key = storage_key.slice(NAMESPACE.length)
                        try
                            value = JSON.parse(storage_value)
                        catch error
                            console.error("Bad configuration value
                                for #{key}: #{storage_value}", error)
                            continue
                        @_setKey(key, value)
                @_synchronise()

            _synchronise: =>
                $http.get("services/configuration")
                    .then(({data}) =>
                        @_synchronised = true
                        # TODO: override values or some such
                    )
                    .catch((response) =>
                        # TODO: retry
                    )


            _setKey: (key, value) =>
                @_values[key] = value
                for observer in (@_observers[key] or [])
                    observer(value)
                $window.localStorage["#{NAMESPACE}#{key}"] =
                    JSON.stringify(value)

            _wrapObserver: (key, type, default_, observer) =>
                return =>
                    value = @_values[key]
                    switch type
                        when @TYPES.STRING then value = value.toString()
                        when @TYPES.BOOLEAN then value = !!value
                        when @TYPES.NUMBER
                            value = Number(value)
                            if isNaN(value)
                                value = 0
                    return observer(value)

            observe: (key, type, default_, observer) =>
                if type not of @TYPES
                    throw new Error("Bad configuration key type: #{type}")
                wrapped = @_wrapObserver(key, type, default_, observer)
                if key not of @_observers
                    @_observers[key] = []
                @_observers[key].push(wrapped)
                if key not of @_values
                    @_setKey(key, default_)
                else
                    wrapped()

                removeObserver = =>
                    index = @_observers[key].indexOf(wrapped)
                    if index >= 0
                        @_observers[key].splice(index, 1)

                return removeObserver

        return new Config()

    return _ =
        name: "Config"
        dependencies: ["$http", "$window"]
        service: factory
