(function (module) { "use strict";


})(angular.module("serverstf", [
    "ngRoute",
    "ngAnimate",
    "serverstf.server"
]));


(function (module) { "use strict";


function HeaderController($scope) {
    var self = this;
    self.class = "foo";
    self.query = "";

    $scope.$watch(
        function () { return self.query; },
        function (new_) {
            if (new_) {
                self.class = "cover-" + new_;
            } else {
                self.class = "";
            }
        }
    );
}


module.controller(
    "HeaderController",
    [
        "$scope",
        HeaderController
    ]);


})(angular.module("serverstf"));
