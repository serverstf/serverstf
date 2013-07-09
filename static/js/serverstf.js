
google.load("visualization", "1", {packages: ["annotatedtimeline"]});

var serverstf = {
	has_geolocation: null,
	
	location: {
		region: null,
		latitude: null,
		longitude: null
	},
	
	api_root: null,
	allow_relist: null,
	csrf_token: null,
	
	active_requests: [],
	request: function (method, path, params, success) {
		// serverstf.request(method, path, success)
		// serverstf.request(method, path, params, success)
		
		if (typeof params === "function" &&
			typeof success === "undefined") {
			success = params;
			params = {};
		}
		
		if (path[0] === "servers") { params.region = serverstf.location.region; }
		
		request_config = {
			type: method,
			dataType: "json",
			headers: {"X-CSRFToken": serverstf.csrf_token},
			url: [serverstf.api_root].concat(path).join("/") + "/",
			data: params,
			error: function (xhr, status, error) {
				console.error(error, xhr.responseText);
			},
			success: success,
			complete: function (xhr) {
				for (var i = 0; i < serverstf.active_requests.length; i++) {
					if (serverstf.active_requests[i] === xhr) {
						serverstf.active_requests.splice(i, 1);
						break;
					}
				}
			}
		}
		
		//console.log(request_config);
		request = $.ajax(request_config);
		serverstf.active_requests.push(request);
		return request;
	},
	
	// serverstf.ServerEntry(id, [jq])
	ServerEntry: function (id, jq) {
		
		this.id = id;
		this.preference = null; // used by Collectiion
		this.distance = -1;
		this.ready = false;
		this.last_update = {
			update: null,
			activity: null,
			players: null
		};
		
		if (typeof jq === "undefined") {
			this.jq = serverstf.ServerEntry.template.source.clone(true);
			this.jq.removeAttr("id");
			this.jq.hide();
		}
		else {
			this.jq = jq;
		}

		this.jq.data("ServerEntry", this);
		
		this.fields = {};
		for (var key in serverstf.ServerEntry.template.fields) {
			this.fields[key] = this.jq.find(
							serverstf.ServerEntry.template.fields[key]);
		}
		
		this.display_mode = null;
		this.display(serverstf.ServerEntry.HIDDEN);
		
		this.name = null;
		this.host = null;
		this.port = null;
		this.player_count = null;
		this.bot_count = null;
		this.max_players = null;
		this.vac_enabled = null;
		this.online = null;
		this.favourited = null;
		
		this.players = [];
		this.activity_chart = null;
		this.activity = new google.visualization.DataTable();
		this.activity.addColumn("datetime", "Date");
		this.activity.addColumn("number", "Player Count");
		this.activity.addColumn("number", "Bot Count");
		
		this.config = {
			alltalk: null,
			teamtalk: null,
			damage_spread: null,
			bullet_spread: null,
			crits: null,
			lowgrav: null,
			cheats: null,
			medieval: null
		};
		
		this.mods = {
			rtd: null,
			randomiser: null,
			quakesounds: null,
			prophunt: null,
			robot: null,
			hunted: null,
			medipacks: null,
			dodgeball: null,
			mge: null,
			goomba: null,
			smac: null,
			hlxce: null,
			soap: null,
			antif2p: null,
			sodstats: null,
			jetpack: null,
			zf: null,
			amplifier: null
		};
		
		this.location = {
			longitude: null,
			latitude: null,
			country: null,
			continent: null
		};
		
	},
	
	tags: {
		"full": function (se) { return se.player_count >= se.max_players },
		"active": function (se) { return se.player_count >= (se.max_players * 0.6) },
		"bots": function (se) { return se.bot_count > 0 },
		"trade": function (se) { return se.map.toLowerCase().startsWith("trade_") },
		"vsh": function (se) { return se.map.toLowerCase().startsWith("vsh_") },
		"mge": function (se) { return se.map.toLowerCase().startsWith("mge_") },
		"jump": function (se) { return se.map.toLowerCase().startsWith("jump_") },
		"surf": function (se) { return se.map.toLowerCase().startsWith("surf_") },
		"mvm": function (se) { return se.map.toLowerCase().startsWith("mvm_") },
		"alltalk": function (se) { return se.alltalk },
		"teamtalk": function (se) { return se.teamtalk },
		"nocrit": function (se) { return !se.crits },
		"nospread": function (se) { return !se.damage_spread },
		"nobulletspread": function (se) { return !se.bullet_spread },
		
		"soap": function (se) { return se.mods.soap === true },
		"rtd": function (se) { return se.mods.rtd === true },
		"stats": function (se) { return se.mods.hlxce === true || se.mods.sodstats === true },
		"robot": function (se) { return se.mods.robot === true },
		"randomiser": function (se) { return se.mods.randomiser === true },
		"prophunt": function (se) { return se.mods.prophunt === true ||
										se.map.toLowerCase().startsWith("ph_") },
		"hunted": function (se) { return se.mods.hunted === true },
		"dodgeball": function (se) { return se.mods.dodgeball === true },
		"quakesounds": function (se) { return se.mods.quakesounds === true },
		"goomba": function (se) { return se.mods.goomba === true },
		"nof2p": function (se) { return se.mods.antif2p === true },
		"jetpack": function (se) { return se.mods.jetpack === true },
		"zombiefortress": function (se) { return se.mods.zf === true },
		"amplifier": function (se) { return se.mods.amplifier === true },
		
		"password": function (se) { return se.password_protected },
		"vac": function (se) { return se.vac_enabled },
		"smac": function (se) { return se.mods.smac === true }
	},
	tag: function (tag, tags) {
		
		if (tag.length < 1) { return null }
		
		jq = $("<li></li>", {text: tag});
		if (typeof tags !== "undefined") { tags.append(jq) }
		
		return jq;
	},
	
	// serverstf.Collection(jq)
	Collection: function (jq) {
		
		var self = this;
		var jq = jq;
		var active = null;
		var update_queue = [];
		
		var update_next = function (self) {
			if (update_queue.length > 0) {
				next = update_queue[0];
				update_queue.splice(0, 1);
				update_queue.push(next);
				
				var se = self[next];
				se.update(se.ready);
			}
			
			if (active !== null) {
				active.update_players();
				active.update_activity();
			}
		}
		setInterval(function () { update_next(self) }, 500);
		
		// NOTE: this prevents the server entry template having more
		// than one class
		selector = (jq.selector + "> ." +
					serverstf.ServerEntry.template.source.attr("class"));
		$(document).on("click", selector, function () {
			if (event.target != this) { return; }
			se = $(this).data("ServerEntry");
			
			if (active !== null) { active.display(serverstf.ServerEntry.NORMAL); }
			se.display(serverstf.ServerEntry.EXPANDED);
			active = se;
		});
		
		var _add = function (self, id) {
			
			if (id in self) { return self[id]; } 
			
			self[id] = new serverstf.ServerEntry(id);
			self[id].preference = -1;
			jq.append(self[id].jq);
			update_queue.splice(0, 0, id);
			
			return self[id];
		}
		var _extend = function (self, ids) {
			for (var i = 0; i < ids.length; i++) {
				self.add(ids[i]);
			}
		}
		var _update_all = function (self) {
			for (var key in self) {
				if (typeof self[key] !== "function") {
					self[key].update();
				}
			}
		}
		var _filter = function (self, tags) {
			var evaluators = []
			
			$.each(tags, function (i, tag) {
				
				var prefix = tag.charAt(0);
				var name = tag.slice(1);
				
				function require(tag) {
					function _require(se) {
						if (!se.has_tag(tag)) {
							se.preference = -1;
						}
					} return _require;
				}
				
				function ignore(tag) {
					function _ignore(se) {
						if (se.has_tag(tag)) {
							se.preference = -1;
						}
					} return _ignore;
				}
				
				function prefer(tag) {
					function _prefer(se) {
						if (se.has_tag(tag) && se.preference !== -1) {
							se.preference++;
						}
					} return _prefer;
				}
				
				function gt(n) {
					n = parseInt(n);
					
					if (isNaN(n)) { return function (se) {}; }
					function _gt(se) {
						if (!(se.player_count > n)) {
							se.preference = -1;
						}
					} return _gt;
				}
				
				function lt(n) {
					n = parseInt(n);
					
					if (isNaN(n)) { return function (se) {}; }
					function _lt(se) {
						if (!(se.player_count < n)) {
							se.preference = -1;
						}
					} return _lt;
				}
				
				if (prefix === "+") { evaluators.push(require(name)); evaluators.push(prefer(name)); }
				else if (prefix === "-") { evaluators.push(ignore(name)); }
				else if (prefix === ">") { evaluators.push(gt(name)); } 
				else if (prefix === "<") { evaluators.push(lt(name)) }
				else { evaluators.push(prefer(tag)); }
				
			});
			
			var ordered = [];
			$.each(self, function (i, se) {
				if (typeof se == "function") { return; }
				if (!se.ready) { return; }
				
				ordered.push(se);
				se.jq.detach();
				
				se.preference = (se.player_count / se.max_players) + (se.favourited ? 1 : 0);
				if (se.distance !== -1) {
					se.preference = se.preference + (1 - (se.distance / (Math.PI * 6371)));
				}
				
				$.each(evaluators, function (i, evaluator) {
					evaluator(se);
					if (se.preference === -1) { return; }
				});
				
			});
			
			ordered.sort(function (a, b) {
				if (a.preference < b.preference) { return 1; }
				if (a.preference > b.preference) { return -1; }
				else { return 0; }
			});
			for (var i = 0; i < ordered.length; i++) {
				jq.append(ordered[i].jq);
				ordered[i].display();
				if (ordered[i].preference === -1) {
					ordered[i].display(serverstf.ServerEntry.HIDDEN);
				}
			}
		}
		
		this.add = function (id) { return _add(self, id) };
		this.extend = function (ids) { return _extend(self, ids) };
		this.update_all = function () { return _update_all(self) };
		this.filter = function (tags) { return _filter(self, tags) };
	}
}

// serverstf.ServerEntry class properties
serverstf.ServerEntry.selector = null;
serverstf.ServerEntry.template = {source: null, fields: null};
serverstf.ServerEntry.activity_chart = {};
serverstf.ServerEntry.update_after = {
	update: 0,
	activity: 0,
	players: 0
};

// Display mode
serverstf.ServerEntry.HIDDEN = 0;
serverstf.ServerEntry.NORMAL = 1;
serverstf.ServerEntry.EXPANDED = 2;

// serverstf.ServerEntry.list(tags)
serverstf.ServerEntry.list = function (tags, cb) {
	
	if (tags.length === 0) { tags = ["*"]; }
	
	if (serverstf.allow_relist) {
		return serverstf.request("GET", 
			["servers", tags.join(","), "search"], cb);
	}
	else {
		cb([]);
		return;
	}
}

// serverstf.ServerEntry methods
serverstf.ServerEntry.prototype.display = function (mode) {
	
	if (this.ready && this.online && this.preference !== -1) {
		this.jq.show();
	}
	else {
		this.jq.hide();
	}
	
	if (typeof mode === "undefined") { return; }
	
	if (mode === serverstf.ServerEntry.EXPANDED) {
		this.fields.detail.slideDown();
	}
	else if (mode === serverstf.ServerEntry.NORMAL) {
		this.fields.detail.slideUp();
	}
	else if (mode === serverstf.ServerEntry.HIDDEN) {
		this.jq.hide();
	}
	
	this.display_mode = mode;
	return mode;
}
serverstf.ServerEntry.prototype.gmaps = function (params) {
	
	params.center = [this.location.latitude, this.location.longitude].join(",");
	query = [];
	for (var key in params) {
		query.push(key + "=" + params[key]);
	}
	
	return "http://maps.googleapis.com/maps/api/staticmap?" + query.join("&");
}
serverstf.ServerEntry.prototype.connect = function () {
	window.open(this.connect_uri());
}
serverstf.ServerEntry.prototype.connect_uri = function () {
	return "steam://connect/" + this.host + ":" + this.port;
}
serverstf.ServerEntry.prototype.update_fields = function () {
	this.fields.name.text(this.name);
	this.fields.player_count.text(this.player_count);
	this.fields.bot_count.text(this.bot_count);
	this.fields.max_players.text(this.max_players);
	this.fields.host.text(this.host);
	this.fields.port.text(this.port);
	this.fields.map.text(this.map);
	
	if (this.favourited) { this.fields.favourite.addClass("saved"); }
	else { this.fields.favourite.removeClass("saved"); }
	
	this.fields.connect.attr("href", this.connect_uri());
	this.fields.location.attr("src", this.gmaps({
														size: "400x200",
														sensor: false,
														zoom: 4
														}));
														
	// Tags
	this.fields.tags.empty();
	for (var tag in serverstf.tags) {
		if (serverstf.tags[tag](this)) {
			this.fields.tags.append($("<li></li>", {text: tag}));
		}
	}
	
	this.display();
	
	if (this.display_mode !== serverstf.ServerEntry.EXPANDED) { return; }
	// ~~~ EXPANDED view only ~~~
	
	// Players table
	var players_table = this.fields.players;
	players_table.find("tr").slice(1).remove();
	$.each(this.players, function (i, player) {
		$("<tr/>").append($("<td/>", {text: player.name}))
			.append($("<td/>", {text: player.score}))
			.append($("<td/>", {text: moment.duration(player.duration, "s").humanize()}))
			.appendTo(players_table);
	});
	
	// Activity chart
	if (this.activity_chart === null) {
		this.activity_chart = new google.visualization.AnnotatedTimeLine(
												this.fields.activity.get(0));
	}	
	this.activity_chart.draw(this.activity,
		serverstf.ServerEntry.activity_chart);
}
serverstf.ServerEntry.prototype.should_update = function () {
	
	now = new Date().getTime();
	o = new Object();
	
	if (!this.ready) { return {update: true, activity: true, players: true}; }
	for (var key in this.last_update) {
		if (this.last_update[key] === null) {
			o[key] = true;
		}
		else {
			o[key] = (now - this.last_update[key].getTime()) > 
				(serverstf.ServerEntry.update_after[key] * 1000)
		}
	}
	
	return o;
}
serverstf.ServerEntry.prototype.update_activity = function () {
	
	if (!this.should_update().activity) { return; }
	
	var self = this;
	serverstf.request("GET", ["servers", this.id, "activity"],
		function (response) {
			self.activity.removeRows(0, self.activity.getNumberOfRows());
			
			$.each(response, function (i, al) {
				self.activity.addRow(
					[new Date(al.timestamp), al.player_count, al.bot_count]
				);
			});
			
			self.last_update.activity = new Date();
			self.update_fields();
		}
	);
}
serverstf.ServerEntry.prototype.update_players = function () {
	
	if (!this.should_update().players) { return; }
	
	var self = this;
	serverstf.request("GET", ["servers", this.id, "players"], 
		function (response) {
			self.players = response;
			self.players.sort(function (a, b) { return b.score - a.score; });
			self.last_update.players = new Date();
			self.update_fields();
		}
	);
}
serverstf.ServerEntry.prototype.update = function (fast) {
	
	if (typeof fast === "undefined") { fast = false; }
	
	if (!this.should_update().update) { return; }
	
	var self = this;
	serverstf.request("GET", ["servers", this.id], {update: fast ? 1 : 0},
		function (response) {
			function _setProperties(object, source) {
				for (var key in source) {
					if (typeof source[key] === "object") {
						_setProperties(object[key], source[key]);
					}
					else {
						object[key] = source[key];
					}
				}
			}
			
			_setProperties(self, response);
			
			if (self.location.latitude === null ||
				self.location.longitude === null ||
				serverstf.location.latitude === null ||
				serverstf.location.longitude === null) {
			
				this.distance = -1;
			}
			
			function toorad4u(degrees) { return degrees * Math.PI / 180; }
			
			var r = 6371;
			
			var slat = toorad4u(self.location.latitude); // 1
			var slon = toorad4u(self.location.longitude); // 1
			var ulat = toorad4u(serverstf.location.latitude); // 2
			var ulon = toorad4u(serverstf.location.longitude); // 2
			
			self.distance = 2 * r * Math.asin(
						Math.sqrt(
							Math.pow(Math.sin((ulat - slat) / 2), 2) +
							Math.cos(slat) *
							Math.cos(ulat) * 
							Math.pow(Math.sin((ulon - slon) / 2), 2)
						)
					);
			
			self.last_update.update = new Date();
			self.ready = true;
			self.update_fields();
		}
	);
}
serverstf.ServerEntry.prototype.favourite = function () {
	
	var self = this;
	serverstf.request("POST", ["servers", this.id, "favourite"],
								function () { self.update(true); });
}
serverstf.ServerEntry.prototype.unfavourite = function () {
	
	var self = this;
	serverstf.request("POST", ["servers", this.id, "unfavourite"], 
								function () { self.update(true); });
}
serverstf.ServerEntry.prototype.has_tag = function (tag) {
	
	if (tag in serverstf.tags) {
		return (serverstf.tags[tag](this));
	}
	
	return false;
}

// Setup
$(window).on("load", function () {
	
	serverstf.has_geolocation = "geolocation" in navigator;
	if (serverstf.has_geolocation) {
		navigator.geolocation.getCurrentPosition(function (pos) {
			serverstf.location.latitude = pos.coords.latitude;
			serverstf.location.longitude = pos.coords.longitude;
		});
	}
	
	serverstf.ServerEntry.selector = "." + serverstf.ServerEntry.template.source.attr("class");
	// ~~~ serverstf ready ~~~

	fav_selector = [
		serverstf.ServerEntry.selector,
		serverstf.ServerEntry.template.fields.favourite
	].join(" ");
	
	$(document).on("click", fav_selector, function () {
		se = $(this)
				.parents(serverstf.ServerEntry.selector)
				.data("ServerEntry");

		if (se.favourited) { se.unfavourite(); }
		else { se.favourite(); }
	});
	
});
