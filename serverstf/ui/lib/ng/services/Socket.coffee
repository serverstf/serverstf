define ->

    class Socket

        constructor: ($timeout) ->
            @_$timeout = $timeout  # lol, no
            @_min_retry_delay = 1000
            @_max_retry_delay = 120000
            @_retry_delay = @_min_retry_delay  # ms
            @_socket = null
            @_buffer = []
            @_handlers = {}
            @on("error", (e) -> console.error("Socket error: #{e}"))
            @_connect()

        isConnected: ->
            return @_socket and @_socket.readyState == WebSocket.OPEN

        _onOpen: =>
            console.info("Socket connection to #{@_socket.url} established!")
            @_retry_delay = @_min_retry_delay
            for args in @_buffer
                @send(args ...)
            @_buffer.length = 0

        _onClose: =>
            console.warn("Socket closed, retrying in #{@_retry_delay / 1000}")
            @_$timeout(@_connect, @_retry_delay)
            @_retry_delay = Math.min(@_retry_delay * 1.5, @_max_retry_delay)

        _onMessage: (message) =>
            envelope = JSON.parse(message.data)
            handlers = @_handlers[envelope.type] or []
            if not handlers.length
                console.warn("Unhandled message of type
                             '#{envelope.type}'", envelope.entity)
            else
                for handler in handlers
                    handler(envelope.entity)

        _connect: ->
            @_socket = new WebSocket("ws://#{window.location.hostname}:9001/")
            @_socket.onopen = @_onOpen
            @_socket.onmessage = @_onMessage
            @_socket.onclose = @_onClose

        send: (type, entity) ->
            if @isConnected()
                @_socket.send(JSON.stringify(
                    type: type
                    entity: entity
                ))
            else
                @_buffer.push([type, entity])

        on: (type, handler) ->
            if type not of @_handlers
                @_handlers[type] = []
            if handler not in @_handlers[type]
                @_handlers[type].push(handler)
            return ->
                @_handlers[type].remove(handler)

        onScoped: (scope, type, handler) ->
            scope.$on("$destroy", @on(type, handler))

    return _ =
        "name": "Socket"
        "dependencies": ["$timeout"]
        "service": Socket
