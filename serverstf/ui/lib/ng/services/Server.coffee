define ->

    factory = ($rootScope, Socket, Modal) ->

        class Server

            constructor: (free, ip, port) ->
                @free = free
                @ip = ip
                @port = port
                @application_id = 440
                @name = ""
                @map = ""
                @tags = []
                @players = 0
                @country = ""

        # Access and track server states.
        #
        # This service maintains a collection of all servers in use. When
        # a server is retrieved from this service it will ensure that a
        # `subscribe` message is sent to the socket so that it starts
        # receiving status updates. A `status` message handler is added to
        # the socket so that the updates are propagated to the corresponding
        # objects automatically.
        #
        # The objects managed by this service are explicitly reference
        # counted. When a server is looked ip via `get` its reference count
        # is incremented. When the caller is finished with the object it must
        # `free` it which decrements the reference count. When the reference
        # count reaches zero an `unsubscribe` message is sent to the socket
        # which will stop all future `status`es for that server.
        #
        # Once a server has been freed it should not be used anymore.
        class ServerService

            constructor: ->
                @_servers = {}  # address : {references : N, server : Server}
                Socket.on("status", @_onStatus)

            # Handle `status` messages.
            #
            # It is possible for a status update be received for a server
            # that is no longer tracked by the service as the update may
            # have occured just before an `unsubscribe` was sent. In these
            # cases a warning is logged but the message is otherwise ignored.
            _onStatus: (entity) =>
                address = @_stringifyAddress(entity.ip, entity.port)
                server = @_servers[address]
                if not server
                    console.warn("Received a status update
                                 for untracked server #{address}")
                    return
                server.server.name = entity.name
                server.server.map = entity.map
                server.server.tags = entity.tags
                server.server.players = entity.players
                server.server.country = entity.country
                if server.server.players.current > 0
                    Modal.open("ServerDetails", {
                        ip: server.server.ip,
                        port: server.server.port,
                    })


            # Convert an IP address and port number to a string.
            #
            # The returned string will be in the conventional `<ip>:<port>`
            # form.
            _stringifyAddress: (ip, port) ->
                return "#{ip}:#{port}"

            # Free a reference to a sever.
            #
            # This decrements the reference count for the server identified
            # by the given IP and port. If the post-decrement reference count
            # is zero then an `unsubscribe` message is sent for the given
            # address and the server is deleted from  collection.
            _free: (ip, port) ->
                address = @_stringifyAddress(ip, port)
                server = @_servers[address]
                if not server
                    console.trace("Apparent double-free of #{address}")
                    return
                server.references -= 1
                if server.references == 0
                    server.removeConnectObservation()
                    Socket.send("unsubscribe", {ip: ip, port: port})
                    delete @_servers[address]
                    return

            # Get a server by IP and port.
            #
            # If the server is not already tracked by the service then it
            # will be created and a `subscribe` message is sent for its
            # address so that the service starts receiving status updates.
            #
            # This increments the reference count of the server, so the caller
            # *must* `free` the object once it's finished with it.
            get: (ip, port) ->
                address = @_stringifyAddress(ip, port)
                if address not of @_servers
                    @_servers[address] =
                        references: 0
                        server: new Server(
                            @_free.bind(@, ip, port), ip, port)
                        removeConnectObservation:
                            Socket.observeConnect(->
                                Socket.send("subscribe", {ip: ip, port: port}))
                server = @_servers[address]
                server.references += 1
                return server.server

        return new ServerService()

    return _ =
        "name": "Server"
        "dependencies": ["$rootScope", "Socket", "Modal"]
        "service": factory
