
prefix_class_map = {
	"+": "require",
	"-": "ignore",
	"<": "less-than",
	">": "more-than"
}

text_class_map = {
	"vsh": "vsh",
	"active": "active",
	"vac": "vac",
	"trade": "trade",
	"mge": "mge"
}

function searchServers(servers, search_tags) {

	function _searchServers() {
		
		var required_tags = [];
		var ignored_tags = [];
		var prefered_tags = []
		var min_players = 0;
		var max_players = 32;
		
		search_tags.children("li").each(function () {
			
			tag = $(this).text();
			if (tag.charAt(0) == "+") {
				required_tags.push(tag.slice(1));
			}
			else if (tag.charAt(0) == "-") {
				ignored_tags.push(tag.slice(1));
			}
			else if (tag.charAt(0) == "<") {
				max_players = parseInt(tag.slice(1));
			}
			else if (tag.charAt(0) == ">") {
				min_players = parseInt(tag.slice(1));
			}
			else {
				prefered_tags.push(tag);
			}
		});
		
		$(servers).find(".server-entry:not(#template)").each(function () {
			
			var se = $(this);
			var sv_required_count = 0;
			
			se.show();
			entry = ServerEntry.fromElement(se);
			if (typeof entry != "undefined") {
				if (entry.data != undefined) {
					entry.preference = entry.data.player_count / entry.data.max_players;
				
					if (entry.data.player_count > max_players ||
						entry.data.player_count < min_players) {
						
						se.hide();
					}
				}
			}
			
			$(this).find(".tags > li").each(function () {
				var tag = $.trim($(this).text());

				if ($.inArray(tag, required_tags) != -1) {
					sv_required_count++;
				}
				else if ($.inArray(tag, ignored_tags) != -1) {
					se.hide();
					return false;
				}
				else if ($.inArray(tag, prefered_tags) != -1) {
					if (typeof entry != "undefined") {
						entry.preference++;
					}
				}
			});
			
			if (sv_required_count < required_tags.length) {
				se.hide();
			}
		});
		
		entries = $(servers).find(".server-entry:visible").detach();
		entries.sort(function (a, b) {
			
			a = ServerEntry.fromElement(a);
			b = ServerEntry.fromElement(b);
			
			if (typeof a == "undefined" || typeof b == "undefined") { return 0; }
			//if (typeof a.data == "undefined" || typeof b.data == "undefined") { return 0; }
			
			if (a.preference < b.preference) { return 1; }
			if (a.preference > b.preference) { return -1; }
			else { return 0; }
			
		});
		$(servers).append(entries);
		
	}

	var a = [];
	search_tags.children("li").each(function () { a.push($(this).text()); });
	ServerEntry.list(a.join(","), _searchServers);
	
}

$(document).ready(function () {
	
	$("#search #input-field").click(function () { $(this).find("input[type=text]").focus() });
	$("#search #input-field input[type=text]").focus(function () { $(this).val("") });
	$("#search #input-field input[type=text]").blur(function () { if ($(this).val().length == 0) $(this).val("type to add tags") });
	$("#search #input-field input[type=text]").keypress(function (event) {
		if (event.which == 13) {
			
			if ($(this).val().length == 0) {
				return;
			}
			
			$("#search .tags").append(makeTag($(this).val()));
			
			$(this).val("");
			searchServers($("#servers"), $("#search .tags"));
			
		}
	});
	
	$("#search .tags").on("click", "li", function () {
		$(this).remove();
		searchServers($("#servers"), $("#search .tags"));
	});
	$(".server-entry .tags").on("click", "li", function () {
		$("#search .tags").append(makeTag("+" + $.trim($(this).text())));
		searchServers($("#servers"), $("#search .tags"));
	});
	
	ServerEntry.autoUpdate.complete = function () { searchServers($("#servers"), $("#search .tags")) }
});

function SEARCH() { searchServers($("#servers"), $("#search .tags")); }
