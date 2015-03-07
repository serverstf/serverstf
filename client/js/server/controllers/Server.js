(function (module) { "use strict";


function ServerController(Server) {
    var self = this;
    self.server = Server.get("192.168.0.2:9001");
}


module.controller(
    "ServerController",
    [
        "Server",
        ServerController,
    ]
);


})(angular.module("serverstf.server"));
