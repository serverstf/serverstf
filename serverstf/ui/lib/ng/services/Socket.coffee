define ->

    factory = ($window, $rootScope, $timeout) ->

        # Communicate over a WebSocket.
        #
        # This service wraps a websocket which is used for communicating with
        # the SVTF websocket server backend.
        #
        # All messages sent and received by the socket are JSON encoded
        # objects. Each message has two fields: a `type` and an `entity`.
        # The `type` field is a string that -- not surprisingly -- identifies
        # the type of message. The type of message also dictates the structure
        # of the `entity` field which can otherwise be any JSON-encodable
        # object.
        #
        # The `Socket` service exposes an API for sending and handling
        # messages. It also transparently handles automatic reconnection and
        # message buffering should the underlying websocket should die for
        # any reason.
        #
        # By default the service will add a single message handler for `error`
        # type messages which simply logs the error in the console.
        class Socket

            constructor: ->
                @_min_retry_delay = 5000
                @_max_retry_delay = 60000
                @_retry_delay = @_min_retry_delay
                @_connect_observations = []
                @_buffer = []
                @_handlers = []
                @_socket = null
                @on("error", (e) -> console.error("Socket error: #{e}"))
                @_connect()

            # Check if the socket is connected.
            isConnected: =>
                return @_socket and @_socket.readyState == WebSocket.OPEN

            # Register a callback to be fired upon connection.
            #
            # When the socket connects all callbacks registered by this
            # function are called. They are passed a single argument which
            # is a reference to the `Socket` service.
            #
            # If the socket is already connected then the callback is invoked
            # immediately.
            #
            # Optionally an Angular scope can be provided as the second
            # argument. When the scope is destroyed the callback will be
            # removed. Alternately the callback can be removed manually by
            # invoking the function returned by this method.
            observeConnect: (handler, scope) =>
                @_connect_observations.push(handler)
                if @isConnected()
                    handler(@)

                removeConnectObservation = =>
                    index = @_connect_observations.indexOf(handler)
                    if index >= 0
                        @_connect_observations.splice(index, 1)

                if scope
                    scope.$on("$destroy", removeConnectObservation)
                return removeConnectObservation

            # Register a handler for messages.
            #
            # The `handler` will be called when any message of the given
            # `type` is received. The handler will be passed the message
            # entity as the sole arguments.
            #
            # As with `observeConnect` an optional Angular scope can be
            # provided which, when destroyed, will unregister the handler.
            #
            # Returns a function which can be used to manually unregister the
            # handler.
            on: (type, handler, scope) =>
                if type not of @_handlers
                    @_handlers[type] = []
                @_handlers[type].push(handler)

                removeHandler = =>
                    index = (@_handlers[handler] or []).indexOf(handler)
                    if index >= 0
                        @_handlers[handler].splice(index, 1)

                if scope
                    scope.$on("$destroy", removeHandler)
                return removeHandler

            # Send a message to the server.
            #
            # If the socket is not current connected then the message will
            # be buffered. When the socket eventually reconnects this buffer
            # will be flushed immediately after all the connection
            # observations have been fired.
            send: (type, entity) =>
                if @isConnected()
                    @_socket.send(JSON.stringify(
                        type: type
                        entity: entity
                    ))
                else
                    @_buffer.push([type, entity])

            # Handle websocket connection event.
            #
            # Invoke all the connection observations and flush the send
            # buffer. The connection retry delay will be reset to the minimum
            # retry delay.
            _onOpen: =>
                console.info(
                    "Socket connection to #{@_socket.url} established!")
                @_retry_delay = @_min_retry_delay
                for handler in @_connect_observations
                    handler(@)
                for args in @_buffer
                    @send(args ...)
                @_buffer.length = 0

            # Handle websocket close event.
            #
            # This will register a timeout that will attempt to reconnect
            # after a delay. Each subsequent call (with a successful
            # intermediary connection) will result in the delay getting
            # longer until the maximum connection retry delay is reached.
            _onClose: =>
                console.warn(
                    "Socket closed, retrying in #{@_retry_delay / 1000}")
                $timeout(@_connect, @_retry_delay)
                @_retry_delay = Math.min(
                    @_retry_delay * 1.5, @_max_retry_delay)

            # Handle websockets error events.
            #
            # Closes the socket. "To be safe."
            _onError: =>
                @_socket.close()

            # Handle received messages.
            #
            # This will invoke all the handlers which are registered for
            # the particular message's type.
            _onMessage: (message) =>
                $rootScope.$applyAsync(=>
                    envelope = JSON.parse(message.data)
                    handlers = @_handlers[envelope.type] or []
                    if not handlers.length
                        console.warn("Unhandled message of type
                                     '#{envelope.type}'", envelope.entity)
                    else
                        for handler in handlers
                            handler(envelope.entity)
                )

            # Attempt to connect to the server.
            _connect: =>
                url = $window._SVTF["socket"];
                @_socket = new WebSocket(url)
                @_socket.onopen = @_onOpen
                @_socket.onmessage = @_onMessage
                @_socket.onerror = @_onError
                @_socket.onclose = @_onClose

        return new Socket()

    return _ =
        "name": "Socket"
        "dependencies": ["$window", "$rootScope", "$timeout"]
        "service": factory
