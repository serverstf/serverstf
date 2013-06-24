
function elementInViewport(el) {
	var top = el.offsetTop;
	var left = el.offsetLeft;
	var width = el.offsetWidth;
	var height = el.offsetHeight;

	while(el.offsetParent) {
		el = el.offsetParent;
		top += el.offsetTop;
		left += el.offsetLeft;
	}

	return (
		top < (window.pageYOffset + window.innerHeight) &&
		left < (window.pageXOffset + window.innerWidth) &&
		(top + height) > window.pageYOffset &&
		(left + width) > window.pageXOffset
	);
}


function reportAjaxError(respone, status, err) {
	console.log("AJAX request failed; " + status + " "+ err);
}

function makeTag(tag) {
	
	tag = $.trim(tag).toLowerCase();
	if (tag.length == 0) { return $(); }
	
	jq = $("<li></li>");
	
	prefix = tag.charAt(0);
	if ($.inArray(prefix, ["+", "-", ">", "<"]) == -1) {
		jq.addClass(tag);
	}
	else {
		jq.addClass(tag.slice(1));
	}
	
	jq.text(tag);
	return jq;
}

TAGS = [
	["full", function (se) { return se.player_count >= se.max_players }],
	["active", function (se) { return se.player_count >= (se.max_players * 0.6) }],
	["bots", function (se) { return se.bot_count > 0 }],
	["trade", function (se) { return se.map.toLowerCase().startsWith("trade_") }],
	["vsh", function (se) { return se.map.toLowerCase().startsWith("vsh_") }],
	["mge", function (se) { return se.map.toLowerCase().startsWith("mge_") }],
	["jump", function (se) { return se.map.toLowerCase().startsWith("jump_") }],
	["surf", function (se) { return se.map.toLowerCase().startsWith("surf_") }],
	["alltalk", function (se) { return se.alltalk }],
	["teamtalk", function (se) { return se.teamtalk }],
	["nocrit", function (se) { return !se.crits }],
	["nospread", function (se) { return !se.damage_spread }],
	["nobulletspread", function (se) { return !se.bullet_spread }],
	
	["soap", function (se) { return $.inArray("soap", se.mods) != -1 }],
	["rtd", function (se) { return $.inArray("rtd", se.mods) != -1 }],
	["stats", function (se) { return $.inArray("hlxce", se.mods) != -1 }],
	["robot", function (se) { return $.inArray("robot", se.mods) != -1 }],
	["randomiser", function (se) { return $.inArray("randomiser", se.mods) != -1 }],
	["prophunt", function (se) { return $.inArray("prophunt", se.mods) != -1 }],
	["hunted", function (se) { return $.inArray("hunted", se.mods) != -1 }],
	["dodgeball", function (se) { return $.inArray("dodgeball", se.mods) != -1 }],
	["quakesounds", function (se) { return $.inArray("quakesounds", se.mods) != -1 }],
	["goomba", function (se) { return $.inArray("goomba", se.mods) != -1 }],
	
	["password", function (se) { return se.password_protected }],
	["vac", function (se) { return se.vac_enabled }],
	["smac", function (se) { return $.inArray("smac", se.mods) != -1 }],
];

function ServerEntry(id, container) {
	
	this.id = id;
	this.data = undefined;
	this.preference = 0;
	
	this.jq = $(".server-entry#template").clone(true);
	this.jq.removeAttr("id");
	this.jq.show();
	
	if (typeof container !== "undefined") {
		$(container).append(this.jq);
	}
	
	this.fields = {
		id: this.jq.find(".id"),
		extended: this.jq.find(".modules"),
		activity_chart: this.jq.find(".activity-chart"),
		player_table: this.jq.find(".player-table"),
		player_count: this.jq.find(".player-count"),
		max_player_count: this.jq.find(".max-player-count"),
		bot_count: this.jq.find(".bot-count"),
		name: this.jq.find(".server-name"),
		ip: this.jq.find(".server-ip"),
		map: this.jq.find(".server-map"),
		location_map: this.jq.find("img.server-location-map"),
		network: this.jq.find(".server-network"),
		network_link: this.jq.find(".server-network-link"),
		extended_view: this.jq.find(".extended-view"),
		connect_link: this.jq.find(".connect-link"),
		fav_icon: this.jq.find(".fav-icon"),
	};
	
	this.activity_chart = null;
	
	this.fields.id.text(this.id);
}

ServerEntry.update_list = {};
ServerEntry.current_extended = null;
ServerEntry.all = {};
ServerEntry.container = null;
ServerEntry.region = null;
ServerEntry.batch_size = null;
ServerEntry.allow_relist = null;

ServerEntry.autoUpdateQueueCount = 0;
ServerEntry.autoUpdateInterval = 30000;
ServerEntry.autoUpdate = function () {
	
	if (ServerEntry.autoUpdateQueueCount < 1) {
		var ids = [];
		for (var id in ServerEntry.all) { ids.push(id); }
		ServerEntry.autoUpdateQueueCount = ids.length;
		
		ServerEntry.updateBatch(ids, function () {
			ServerEntry.autoUpdateQueueCount = ServerEntry.autoUpdateQueueCount - ServerEntry.batch_size;
			if (typeof ServerEntry.autoUpdate.complete === "function") {
				ServerEntry.autoUpdate.complete();
			}
		});
	}
}
ServerEntry.autoUpdate.complete = undefined;

ServerEntry.initialise = function (ids, container) {
	// Registers event handlers and creates a set of entries from the
	// array of IDs in the given container.
	
	ServerEntry.container = container;
	
	$(".server-entry").click(function (event) {
		
		if (event.target != this) { return; }
		
		if (ServerEntry.current_extended !== null
				&& !ServerEntry.current_extended.jq.is(this)) {
			
			ServerEntry.current_extended.fields.extended.slideUp(1000);
		}
		
		ServerEntry.current_extended = ServerEntry.all[$(this).find(".id").text()];
		$(this).find(".modules").slideDown(1000, function () { ServerEntry.current_extended.updateAll() });
	});
	
	$(".server-entry .fav-icon").click(function () {
		ServerEntry.all[$(this).parents(".server-entry").find(".id").text()].toggleFavourite();
	});
	
	// Current entry/viewport update
	setInterval(function () {
		var se = ServerEntry.current_extended;
		if (se !== null) {
			se.update();
		}
	}, 10000);
	
	// Update all
	setInterval(ServerEntry.autoUpdate, ServerEntry.autoUpdateInterval);
	
	// Initial IDs
	for (var i = 0; i < ids.length; i++) { ServerEntry.add(ids[i]); }
	ServerEntry.updateBatch(ids);
	
	
}

ServerEntry.add = function (id) {
	
	if (!(id.toString() in ServerEntry.all)) {
		se = new ServerEntry(id, ServerEntry.container);
		ServerEntry.all[se.id.toString()] = se;
	}
}

ServerEntry.list = function(tags, complete) {
	
	if (ServerEntry.allow_relist) {
		console.log("/api/list/" + ServerEntry.region + "/" + tags);
		
		$.ajax({
			dataType: "json",
			url: "/api/list/" + ServerEntry.region + "/" + tags,
			error: reportAjaxError,
			success: function (response) {
				$.each(response, function(i, id) {
					ServerEntry.add(id);
				});
				ServerEntry.updateBatch(response, complete);
			},
			complete: complete
		});
	}
	else {
		complete();
	}
	
}

ServerEntry.updateBatch = function (ids, complete) {
	
	var i, batch;
	for (i = 0; i < ids.length; i += ServerEntry.batch_size) {
		batch = ids.slice(i, i+ServerEntry.batch_size);
		console.log("/api/server/" + batch.join(","));
		$.ajax({
			dataType: "json",
			url: "/api/server/" + batch.join(","),
			error: reportAjaxError,
			success: function (response) {
				$.each(response, function () {
					se = ServerEntry.all[this.id];
					if (typeof se != "undefined") {
						se.setData(this);
					}
				});
			},
			complete: complete
		});
	}
	
}

ServerEntry.fromElement = function (elt) {
	return ServerEntry.all[$(elt).find(".id").text()];
}

ServerEntry.prototype.updateAll = function () {
	this.update();
	this.updatePlayerList();
	this.updateActivityChart();
}

ServerEntry.prototype.setData = function (response) {
	
	var self = this;
	self.data = response;

	if (!response["online"]) { self.jq.addClass("offline"); }
	else { self.jq.removeClass("offline"); }
	
	if (response["favourited"]) { self.fields.fav_icon.addClass("saved"); }
	else { self.fields.fav_icon.removeClass("saved"); }
	
	self.fields.player_count.text(response["player_count"]);
	self.fields.max_player_count.text("/"+response["max_players"]);
	
	if (response["bot_count"] > 0) {
		self.fields.bot_count.text(response["bot_count"] + " bots");
	}
	else {
		self.fields.bot_count.hide();
	}
	
	self.fields.name.text(response["name"]);
	self.fields.ip.text(response["host"]+":"+response["port"]);
	self.fields.map.text(response["map"]);
	self.fields.connect_link.attr("href", "steam://connect/"+response["host"]+":"+response["port"]);
	
	if (response["location"]["latitude"] !== null && response["location"]["longitude"] !== null) {
		self.fields.location_map.attr("src", "http://maps.googleapis.com/maps/api/staticmap?center="+response["location"]["latitude"]+","+response["location"]["longitude"]+"&zoom=4&size=400x200&sensor=false");
	}
	
	tags = self.jq.find("ul.tags");
	tags.empty();
	$.each(TAGS, function () {
		if (this[1](response)) {
			tags.append(makeTag(this[0]));
		}
	});
	
	if (response["network"] !== null) {
		$.ajax({
			dataType: "json",
			url: "/api/network/" + response["network"],
			error: reportAjaxError,
			success: function (response) {
				self.fields.network.show();
				self.fields.network_link.attr("href", response["link"]);
				self.fields.network_link.text(response["name"]);
			}
		});
	}
	
}

ServerEntry.prototype.update = function () {
	var self = this;
	
	self.fields.id.text(self.id);
	ServerEntry.updateBatch([self.id]);
}

ServerEntry.prototype.updatePlayerList = function () {
	
	var self = this;
	
	$.ajax({
		dataType: "json",
		url: "/api/server/" + self.id + "/players",
		error: reportAjaxError,
		success: function (players) {
			
			self.fields.player_table.find("tr").slice(1).remove();
			
			players.sort(function (a, b) { return b.score - a.score; });
			$.each(players, function (i, player) {
				
				row = $("<tr/>");
				
				name_ = $("<td/>", {text: player["name"]});
				score = $("<td/>", {text: player["score"]});
				duration = $("<td/>", {text: moment.duration(player["duration"], "s").humanize() });
				
				row.append(name_);
				row.append(score);
				row.append(duration);
				
				self.fields.player_table.append(row);
			});
			
			self.fields.player_table.find("tr:even").slice(1).addClass("row");
		}
	});
	
}

ServerEntry.prototype.updateActivityChart = function () {
	
	var self = this;
	
	$.ajax({
		dataType: "json",
		url: "/api/server/" + self.id + "/activity",
		error: reportAjaxError,
		success: function (activity) {
		
			var data = new google.visualization.DataTable();
			data.addColumn("datetime", "Date");
			data.addColumn("number", "Player Count");
			data.addColumn("number", "Bot Count");
			
			$.each(activity, function (i, act) {
				data.addRow([new Date(act.time * 1000.0), act.player_count - act.bot_count, act.bot_count]);
			});
			
			// FIXME: memory leak seemingly coming from the chart
			if (self.activity_chart === null) {
				self.activity_chart =  new google.visualization.AnnotatedTimeLine(self.fields.activity_chart.get(0));
			}
			self.activity_chart.draw(data, {
				displayLegendDots: false,
				displayLegendValues: false,
				displayRangeSelector: false,
				displayZoomButtons: false,
				colors: [
					"#404040",
					"#9F9F9F"
					],
				fill: 35,
				max: 32,
				min: 0
			});
		}
	});

}

ServerEntry.prototype.toggleFavourite = function () {
	
	var self = this;
	
	if (self.fields.fav_icon.hasClass("saved")) { action = "/unfavourite"; }
	else { action = "/favourite"; }
	
	$.ajax({
		dataType: "json",
		url: "/api/server/" + self.id + action,
		error: reportAjaxError,
		complete: function () {
			self.update();
		}
	});
	
}


function SHOW_ALL() { $(".server-entry").show(); }
