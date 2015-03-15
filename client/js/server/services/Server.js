(function (module) { "use strict";


function parseAddress(address_string) {
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
    return {ip: ip, port: port};
}



function Server(address) {
    var self = this;
    _.assign(self, parseAddress(address));
}


Server.prototype.update = function update(status) {
    var self = this;
    self.name = status.name;
    self.map = status.map;
    self.max_player_count = status.players.max;
    self.player_count = status.players.real;
    self.bot_count = status.players.bots;
    self.tags = new Set(status.tags);
    console.log(status, self);
}


function ServerService(Socket) {
    var self = this;
    var servers = {};

    Socket.on("status", function onStatusUpdate(status) {
        var server_key = (status.address.ip
                          + ":" + status.address.port.toString());
        servers[server_key].update(status);
    });

    self.get = function getServer(address) {
        if (!(address in servers)) {
            Socket.send("subscribe", [address.ip, address.port]);
            servers[address] = new Server(address);
        }
        return servers[address];
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
