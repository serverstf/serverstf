define ->

    factory = ($rootScope, Socket) ->

        class Server

            constructor: (free, ip, port) ->
                @free = free
                @ip = ip
                @port = port
                @application_id = 440
                @name = ""
                @map = ""
                @tags = []
                @players =
                    scores: []
                    current: 0
                    max: 0
                    bots: 0
                @country = null
                @latitude = null
                @longitude = null

            hasLocation: =>
                return @country != null and
                    @latitude != null and @longitude != null

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
                server.server.latitude = entity.latitude
                server.server.longitude = entity.longitude


            # Convert an IP address and port number to a string.
            #
            # The returned string will be in the conventional `<ip>:<port>`
            # form.
            _stringifyAddress: (ip, port) ->
                return "#{ip}:#{port}"

            # Parse a stringified address.
            #
            # This takes an address string in the form `<ip>:<port>` and
            # returns an object with corresponding `ip` and `port` fields.
            # The `port` will be converted to a number. The `ip` is left in
            # the IPv4 dotted-decimal form as a string.
            #
            # Throws an error if the address cannot be parsed.
            parseAddress: (string) ->
                # TODO: Validate and throw
                [ip, port_string] = string.split(":")
                return ip: ip, port: parseInt(port_string)



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
            # *must* `free` the object once it's finished with it. Alternately
            # the caller may provide an Angular scope. When the scope is
            # destroyed the server will be freed. This saves having to
            # manually free it.
            get: (ip, port, scope) ->
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
                if scope
                    scope.$on("$destroy", server.free)
                return server.server

        return new ServerService()

    return _ =
        "name": "Server"
        "dependencies": ["$rootScope", "Socket"]
        "service": factory
