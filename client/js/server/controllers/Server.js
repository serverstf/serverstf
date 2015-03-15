(function (module) { "use strict";


function ServerController($scope, $timeout, Server) {
    var self = this;
    self.server = Server.get("94.23.226.212:2055");

    $scope.$watch(
        function () { return self.server; },
        function (server) {
            self.server = server;
        }
    );
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
