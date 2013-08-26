
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
	
	// Modal
	modal = $("#modal");
	modal_win = $("#modal > div");
	
	$(window).resize(function () {
		modal_win.css({
			top: ($(this).height() / 4) - (modal_win.height() / 2),
			left: ($(this).width() / 2) - (modal_win.width() / 2)
		});
	});
	
	modal.click(function () {
		if (modal.is(":visible")) {
			$("a#modal-close").click();
		}
	});
	
	$("a.modal-invoke").click(function () {
		
		modal_id = $(this).attr("href").split("#")[1];
		modal_cfg = $(".modal#modal-" + modal_id);
		if (modal_cfg.length !== 1) {
			return;
		}
		
		$("#modal-title").text(modal_cfg.find(".title").text());
		$("#modal-icon").addClass(modal_cfg.find(".icon").text());
		$("#modal-content").empty().append(modal_cfg.find(".content").clone());
		
		$(window).trigger("resize");
		modal.fadeIn();
		$(window).trigger("resize");
		
	});
	
	$("a#modal-close").click(function () {
			$("#modal").hide();
	});
	
});
