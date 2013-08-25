
String.prototype.startsWith = function (sub) {
	return this.slice(0, sub.length) == sub;
}

$(document).ready(function () {
	
	if (typeof document.fixed_header == "undefined") {
		document.fixed_header = false;
	}
	
	$("#header #user-controls a > span:last-child").hide();
	
	$("#header #user-controls a").hover(
		function () {
			$(this).children("span:last-child").show();
		},
		function () {
			$(this).children("span:last-child").hide();
		}
	);
	
	$(window).scroll(function () {
		if (!document.fixed_header) {
			if ($(window).scrollTop() == 0) {
				$("#header").removeClass("fixed");

			}
			else {
				$("#header").addClass("fixed");
			}
		}
	});
	
});
