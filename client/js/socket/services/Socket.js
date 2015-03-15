(function (module) {


function Socket($rootScope, $timeout, $location) {
    var self = this;
    var event_prefix = "Socket.";
    var min_retry_delay = 5000;
    var max_retry_delay = 120000;
    var retry_delay = min_retry_delay;  // ms
    var socket;
    var buffer = [];

    function onSocketOpen() {
        console.info("Socket connection to " + socket.url + " established!");
        retry_delay = min_retry_delay;
        buffer.forEach(function (args) {
            self.send.apply(self, args);
        });
        buffer.length = 0;
    }

    function onSocketMessage(message) {
        var envelope = JSON.parse(message.data);
        if (envelope.type === "error") {
            console.error("ServiceError", envelope.entity)
        } else {
            if (!_.isString(envelope.type)) {
                // Throw instead?
                console.error(
                    "Bad envelope: 'type' field wrong type", envelope);
                return;
            }
            if (_.isUndefined(envelope.entity)) {
                console.error(
                    "Base envelope: 'entity' is undefined", envelope);
                return;
            }
            $rootScope.$broadcast(
                event_prefix + envelope.type, envelope.entity);
        }
    }

    function onSocketClose() {
        console.warn("Socket closed, retrying in " + retry_delay / 1000);
        $timeout(function reconnect() {
            connect();
        }, retry_delay);
        retry_delay = Math.min(retry_delay * 1.5, max_retry_delay);
    }

    function connect() {
        socket = new WebSocket("ws://" + $location.host() + ":9001/server");
        socket.onopen = onSocketOpen;
        socket.onmessage = onSocketMessage;
        socket.onclose = onSocketClose;
    }

    Object.defineProperty(self, "connected", {
        get: function getConnectionStatus() {
            return (typeof socket !== "undefined"
                    && socket.readyState === WebSocket.OPEN);
        }
    });

    self.send = function send(type, entity) {
        if (self.connected) {
            socket.send(JSON.stringify({type: type, entity: entity}));
        } else {
            buffer.push([type, entity]);
        }
    }

    self.on = function registerHandler(type, handler) {
        return $rootScope.$on(event_prefix + type, function wrapper() {
            return handler.apply(
                self, Array.prototype.slice.call(arguments, 1));
        });
    };

    connect();
}


module.service("Socket", [
    "$rootScope",
    "$timeout",
    "$location",
    Socket,
]);

})(angular.module("serverstf.socket"));
