
$(document).ready(function () {
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
		if ($(window).scrollTop() == 0) {
			$("#header").removeClass("fixed");

		}
		else {
			$("#header").addClass("fixed");
		}
	});
	
});
