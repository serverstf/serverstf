define ->

    factory = ->

        class Config

            constructor: ->
                @TYPES = {}
                for type in ["string", "number", "boolean"]
                    @TYPES[type.toUpperCase()] = type.toUpperCase()
                @_values = {}
                @_observers = {}  # key : [observer, ...]

            _setKey: (key, value) =>
                @_values[key] = value
                for observer in (@_observers[key] or [])
                    observer(value)

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
        service: factory
