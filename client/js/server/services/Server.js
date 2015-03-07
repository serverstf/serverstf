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


function ServerService(Socket) {
    var self = this;
    var servers = {};

    self.get = function getServer(address) {
        if (!(address in servers)) {
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
