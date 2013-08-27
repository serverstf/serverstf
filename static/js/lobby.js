
// depends on serverstf.js

var lobby = {
	NONE: 0,
	SIXES: 1,
	HIGHLANDER: 2,
	ULTIDUO: 3,
	
	SCOUT: 1,
	SOLDIER: 2,
	PYRO: 3,
	DEMO: 4,
	HEAVY: 5,
	ENGY: 6,
	MEDIC: 7,
	SNIPER: 8,
	SPY: 9,
	POCKET: 10,
	ROAMER: 11,
	
	roles: {},
	
	party_overview: null,
	
	users: {},
	_User: function (id) {
		this.id = id;
		this.profile_name = "";
		this.avatar = "";
		this.steam_id = "";
		
		this.jqs = [];
		
		this.update();
	},
	User: function (id) {
		if (!(id in lobby.users)) {
			lobby.users[id] = new lobby._User(id);
		}
		
		return lobby.users[id];
	},
	
	party: null,
	Party: function (id) {
		this.id = id;
		this.map = "";
		this.type = 0;
		this.config = 0;
		this.members = [];
		
		this.update();
	}
};

// lobby constants
lobby.roles[lobby.NONE] = [
	lobby.SCOUT,
	lobby.SOLDIER,
	lobby.PYRO,
	lobby.DEMO,
	lobby.HEAVY,
	lobby.ENGY,
	lobby.MEDIC,
	lobby.SNIPER,
	lobby.SPY,
	lobby.POCKET,
	lobby.ROAMER,
];
lobby.roles[lobby.SIXES] = [
	lobby.SCOUT,
	lobby.POCKET,
	lobby.ROAMER,
	lobby.DEMO,
	lobby.MEDIC,
];
lobby.roles[lobby.HIGHLANDER] = [
	lobby.SCOUT,
	lobby.SOLDIER,
	lobby.PYRO,
	lobby.DEMO,
	lobby.HEAVY,
	lobby.ENGY,
	lobby.MEDIC,
	lobby.SNIPER,
	lobby.SPY,
];
lobby.roles[lobby.ULTIDUO] = [
	lobby.POCKET,
	lobby.MEDIC,
];

// lobby.User properties
lobby.User.template = {source: null, fields: null};

// lobby._User methods
lobby._User.prototype.update = function () {
	var self = this;
	
	serverstf.request("GET", ["users", this.id], function (response) {
		self.profile_name = response.profile_name;
		self.avatar = response.avatar;
		self.is_admin = response.is_admin;
		self.steam_id = response.steam_id;
		
		self.update_user_cards();
	});
}

lobby._User.prototype.update_user_cards = function () {
	
	for (var i = 0; this.jqs.length; i++) {
		jq = this.jqs[i];
		
		jq.find(lobby.User.template.fields.profile_name).text(this.profile_name);
		jq.find(lobby.User.template.fields.avatar).attr("src", this.avatar);
		
	}
}

lobby._User.prototype.get_user_card = function () {
	// TODO: be careful of leak
	
	var jq = lobby.User.template.source.clone();
	jq.removeClass("template");
	jq.data("_User", this);
	
	this.jqs.push(jq);

	return jq;
}

// lobby.Party methods
lobby.Party.prototype.update = function () {
	var self = this;
	
	serverstf.request("GET", ["parties", self.id], function (response) {
		self.map = response.map;
		self.type = response.type === null ? 0 : response.type;
		self.config = response.config;
		self.members = [];
		
		for (var i = 0; i < response.members.length; i++) {
			self.members.push(lobby.User(response.members[i]));
		}
		
		lobby.party_overview.trigger("lobby.update_overview");
	});
	
}

lobby.init = function () {
	lobby.party_overview.on("lobby.update_overview", function (e) {
		
		var cards = {};
		$("#party-members .user-card").each(function () {
			user = $(this).data("_User");
			if ($.inArray(user, lobby.party.members) == -1) {
				$(this).fadeOut(function () {
					$(this).remove();
				});
			}
			else {
				cards[user.id] = true;
			}
		});
		
		for (var i = 0; i < lobby.party.members.length; i++) {
			var member = lobby.party.members[i];
			
			if (!(member.id in cards)) {
				var card = member.get_user_card();
				card.hide();
				$("#party-members").prepend(card);
				card.fadeIn();
			}
		}
		
		if ($("#party-members .user-card").length > 1) {
			$("#party-members #solo-hint").hide();
		}
		else {
			$("#party-members #solo-hint").show();
		}
		
		// Filter roles list
		$("select#id_roles > option").each(function () {
			var val = parseInt($(this).attr("value"));
			if ($.inArray(val, lobby.roles[lobby.party.type]) === -1) {
				$(this).attr("disabled", "disabled");
			}
			else {
				$(this).removeAttr("disabled");
			}
		});
		
		// Set type
		$("select#id_type > option").each(function () {
			// TODO: type == 0
			if (parseInt($(this).val()) == lobby.party.type) {
				$(this).prop("selected", true);
			}
		});
		
		// Set config
		$("select#id_config > option").each(function () {
			// TODO:config == null
			if ($(this).val() == lobby.party.config) {
				$(this).prop("selected", true);
			}
		});
		
		// Set map
		$("input#id_map").val(lobby.party.map);
		
	});
	
	setInterval(function () { lobby.party.update() }, 5000);
};

$(window).resize(function () {
	$("#main").height($(this).height() - $("#header").height());
	$("#party-members").css("top", $("#party-config").height() + parseInt($("#party-config").css("margin-bottom")) + 6);
});
