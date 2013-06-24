
var serverstf = {
	region: null,
	api_root: null,
	allow_relist: null,
	
	active_requests: [],
	request: function (method, path, success) {
		
		request_config = {
			type: method,
			dataType: "json",
			url: [serverstf.api_root].concat(path).join("/"),
			data: {
				region: serverstf.region
			},
			success: success,
			complete: function (jqXHR) {
				// FIXME: doesn't actually remove from active_requests
				for (var i = 0; i < serverstf.active_requests.length; i++) {
					if (serverstf.active_requests[i] === jqXHR) {
						serverstf.active_requests.slice(i, 1);
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
	
	// serverstf.list(tags)
	list: function (tags, cb) {
		
		if (serverstf.allow_relist) {
			return serverstf.request("GET", 
				["servers", tags.join(","), "search"], cb);
		}
		else {
			cb([]);
			return;
		}
	},
	
	// serverstf.ServerEntry(id, [jq])
	ServerEntry: function (id, jq) {
		this.id = id;
		
		if (jq === undefined) {
			this.jq = serverstf.ServerEntry.template.source.clone(true);
			this.jq.removeAttr("id");
			this.jq.hide();
		}
		else {
			this.jq = jq;
		}
		
		this.fields = {};
		for (var key in serverstf.ServerEntry.template.fields) {
			this.fields[key] = this.jq.find(
							serverstf.ServerEntry.template.fields[key]);
		}
		
		this.name = null;
		this.host = null;
		this.port = null;
		this.player_count = null;
		this.bot_count = null;
		this.max_players = null;
		this.vac_enabled = null;
		this.online = null;
		
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
			soap: null
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
		"alltalk": function (se) { return se.alltalk },
		"teamtalk": function (se) { return se.teamtalk },
		"nocrit": function (se) { return !se.crits },
		"nospread": function (se) { return !se.damage_spread },
		"nobulletspread": function (se) { return !se.bullet_spread },
		
		"soap": function (se) { return se.mods.soap === true },
		"rtd": function (se) { return se.mods.rtd === true },
		"stats": function (se) { return se.mods.hlxce === true },
		"robot": function (se) { return se.mods.robot === true },
		"randomiser": function (se) { return se.mods.randomiser === true },
		"prophunt": function (se) { return se.mods.prophunt === true },
		"hunted": function (se) { return se.mods.hunted === true },
		"dodgeball": function (se) { return se.mods.dodgeball === true },
		"quakesounds": function (se) { return se.mods.quakesounds === true },
		"goomba": function (se) { return se.mods.goomba === true },
		
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
				
				self[next].update();
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
			
			if (active !== null) { active.fields.detail.slideUp(); }
			se.fields.detail.slideDown();
			active = se;
		});
		
		var _add = function (self, id) {
			self[id] = new serverstf.ServerEntry(id);
			jq.append(self[id].jq);
			self[id].jq.data("ServerEntry", self[id]);
			update_queue.push(id);
			
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
			console.log();
		
		}
		var _filter = function (self, tags) {
			var required = [];
			var ignored = [];
			var prefered = [];
			
			$.each(tags, function (i, tag) {
				
				var prefix = tag.charAt(0);
				var name = tag.slice(1);
				
				if (prefix === "+") { required.push(name); }
				else if (prefix === "-") { ignored.push(name); }
				else if (prefix === ">") { } // TODO:
				else if (prefix === "<") { } // TODO:
				else { prefered.push(tag); }
				
			});

			$.each(self, function (i, se) {
				if (typeof se == "function") { return; }
				
				se.jq.show();
				$.each(required, function (i, tag) {
					if (tag in serverstf.tags) {
						if (!serverstf.tags[tag](se)) {
							se.jq.hide();
							return;
						}
					}
				});
				
				$.each(ignored, function (i, tag) {
					if (tag in serverstf.tags) {
						if (serverstf.tags[tag](se)) {
							se.jq.hide();
							return;
						}
					}
				});
				
				// TODO: prefered
				// TODO: > <
				
			});
		}
		
		this.add = function (id) { return _add(self, id) };
		this.extend = function (ids) { return _extend(self, ids) };
		this.update_all = function () { return _update_all(self) };
		this.filter = function (tags) { return _filter(self, tags) };
	}
}

serverstf.ServerEntry.template = {source: null, fields: null};
serverstf.ServerEntry.prototype.update_fields = function () {
	this.fields.name.text(this.name);
	this.fields.player_count.text(this.player_count);
	this.fields.bot_count.text(this.bot_count);
	this.fields.max_players.text(this.max_players);
	this.fields.host.text(this.host);
	this.fields.port.text(this.port);
	
	this.fields.tags.empty();
	for (var tag in serverstf.tags) {
		if (serverstf.tags[tag](this)) {
			this.fields.tags.append($("<li></li>", {text: tag}));
		}
	}
	
	if (this.online) { this.jq.show(); }
	else { this.jq.hide(); }
}
serverstf.ServerEntry.prototype.update = function () {
	
	var self = this;
	serverstf.request("GET", ["servers", this.id], function (response) {
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
		self.update_fields();
	});
}
