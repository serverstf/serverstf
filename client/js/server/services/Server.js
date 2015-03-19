/// A service for accessing server states.
(function (module) { "use strict";


function Address(ip, port) {
    this.ip = ip;
    this.port = port;
}


Address.parse = function parseAddress(address_string) {
    var ip;
    var port;
    if (typeof address_string !== "string") {
        address_string = address_string.toString();
    }
    var splat = address_string.split(":", 2);
    if (splat.length < 2) {
        ip = splat[0];
        port = 27015;
    } else {
        ip = splat[0];
        port = splat[1];
    }
    port = parseInt(port);
    if (!_.isFinite(port)) {
        throw "Port number '" + port + "' is not finite.";
    }
    // TODO: Do some primitive validation
    return new Address(ip, port);
};


Address.prototype.toString = function formatAddress() {
    return this.ip + ":" + this.port.toString();
};



function Server(address) {
    var self = this;
    self.address = address;
}


Server.prototype.update = function update(status) {
    var self = this;
    self.name = status.name;
    self.map = status.map;
    self.max_player_count = status.players.max;
    self.player_count = status.players.real;
    self.bot_count = status.players.bots;
    self.tags = status.tags;
    console.log(status, self.tags);
}


/// Manages server states.
///
/// Each server is uniquely identified by its address -- the IP and port
/// combination. When a server's state is first requested by its address,
/// this service subscribes to its status updates via the websocket server.
/// It returns an object which represents the most up-to-date state for the
/// given server.
function ServerService(Socket) {
    var self = this;
    var servers = {};

    Socket.on("status", function onServerStatus(status) {
        var address = new Address(status.address.ip, status.address.port);
        var server_key = address.toString();
        if (server_key in servers) {
            servers[server_key].server.update(status);
            servers[server_key].scopes.forEach(function (scope) {
                scope.$apply();
            });
        }
    });

    /// Get a server by address.
    ///
    /// A server address as a string should be given for the server state
    /// being requested. The string should be in the conventional
    /// <ip>:<port> form, where <ip> is a dotted-decimal representation of an
    /// IPv4 address.
    ///
    /// Server status objects are continuously updated whilst they exist.
    ///
    /// Additionally, an Angular scope object should be given. This scope is
    /// used to determine the life time of the server status object. Whilst
    /// one more of the given scopes exists so will the corresponding server
    /// status object. However, once all the scopes have been destroyed then
    /// the ServerService will eventually unsubscribe from updates for the
    /// server.
    ///
    /// Whenever a server status is updated then all scopes bound to that
    /// server will have $apply called on them so that changes can be
    /// immediately relfected in the view.

    // TODO: Should probably return a promise that resolves to the status
    // object when the first update is recieved.
    self.get = function getServer(address, scope) {
        var address = Address.parse(address);
        var server_key = address.toString();

        if (!(server_key in servers)) {
            var server = new Server(address);
            Socket.send("subscribe", [address.ip, address.port]);
            servers[server_key] = {
                server: server,
                scopes: new Set(),
            };
        }
        servers[server_key].scopes.add(scope);

        scope.$on("$destroy", function decRef() {
            servers[server_key].scopes.remove(scope);
            if (servers[server_key].scopes.size === 0) {
                Socket.send("unsubscribe", [address.ip, address.port]);
                delete servers[server_key];
            }
        });

        return servers[server_key].server;
    };
}


module.service(
    "Server",
    [
        "Socket",
        ServerService,
    ]
);


})(angular.module("serverstf.server"));
