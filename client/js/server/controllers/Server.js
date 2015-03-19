(function (module) { "use strict";


function ServerController($scope, $timeout, Server) {
    var self = this;
    self.servers = [];

    var server = Server.get("94.23.226.212:2055", $scope);
    self.servers.push(server);
}


module.controller(
    "ServerController",
    [
        "$scope",
        "$timeout",
        "Server",
        ServerController,
    ]
);


})(angular.module("serverstf.server"));
