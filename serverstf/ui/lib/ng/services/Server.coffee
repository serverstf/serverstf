define ->

    factory = ($rootScope, Socket) ->

        class Server
            constructor: (ip, port) ->
                @ip = ip
                @port = port
                @name = ""
                @map = ""
                @players = 0
                @country = ""

        class ServerService
            constructor: ->
                @_servers = {}
                Socket.on("status", @_onStatus)

            _onStatus: (entity) =>
                address = @_stringifyAddress(entity.ip, entity.port)
                server = @_servers[address]
                if not server
                    console.warn("Received a status update
                                 for untracked server #{address}")
                    return
                server.name = entity.name
                server.map = entity.map
                server.players = entity.players
                server.country = entity.country
                $rootScope.$digest()

            _stringifyAddress: (ip, port) ->
                return "#{ip}:#{port}"

            get: (ip, port) ->
                address = @_stringifyAddress(ip, port)
                if address not of @_servers
                    @_servers[address] = new Server(ip, port)
                    Socket.send("subscribe", {ip: ip, port: port})
                return @_servers[address]

        return new ServerService()

    return _ =
        "name": "Server"
        "dependencies": ["$rootScope", "Socket"]
        "service": factory
