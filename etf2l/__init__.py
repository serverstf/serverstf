
import xml.etree.ElementTree as etree
import urllib2
import urllib
import urlparse
import re

def steamid(steamid):
	"""
		Utility to convert SteamID instances to those appropriate for
		the ETF2L API.
	"""
	return str(steamid).split("_")[-1]

class Resource(object):
	
	def __init__(self, **params):
		
		self.parameters = {}
		for param in self.__class__.parameters:
			
			try:
				self.parameters[param["key"]] = str(params[param["key"]])
			except KeyError:
				if param["required"]:
					raise KeyError("Missing parameter '{}'".format(param["key"]))
	
	@property
	def uri(self):
		"""
			Returns the path and query segments of the URI for the
			specifci resource.
		"""
		
		return self.__class__.path + "?" + urllib.urlencode(self.parameters, "")

class Player(Resource):
	
	path = "/player/"
	parameters = (
					{
					"key": "id",
					"required": False,
					},
					{
					"key": "steamid",
					"required": False
					}
				)
	
	class ETF2LTeam(object):
		
		@classmethod
		def from_xml(cls, xml):
			
			kwargs = {}
			kwargs["id"] = int(xml.attrib["id"])
			kwargs["name"] = xml.attrib["name"]
			kwargs["type"] = xml.attrib["type"]
			
			return cls(**kwargs)
			
		def __init__(self, **kwargs):
			
			self.id = int(kwargs["id"])
			self.name = kwargs["name"]
			self.type = kwargs["type"]
	
	class ETF2LPlayer(object):
		
		@classmethod
		def from_xml(cls, xml):
			
			kwargs = {}
			player = xml.find("player")
			
			kwargs["id"] = int(player.attrib["id"])
			kwargs["steamid"] = player.attrib["steamid"]
			kwargs["username"] = player.find("username").text
			kwargs["displayname"] = player.find("displayname").text
			
			kwargs["teams"] = []
			for team in player.findall("teams/team"):
				kwargs["teams"].append(Player.ETF2LTeam.from_xml(team))
			
			return cls(**kwargs)
			
		def __init__(self, **kwargs):
			
			self.id = kwargs["id"]
			self.steamid = kwargs["steamid"]
			self.username = kwargs["username"]
			self.displayname = kwargs["displayname"]
			self.teams = kwargs["teams"]
			
	response = ETF2LPlayer
	
class ETF2L(object):
	"""
		Provides a limited interface to the ETF2L XML API as described 
		here: http://etf2l.org/about/xml-api/
	"""
	
	API_ROOT = "http://etf2l.org/feed/"
	
	def request(self, resource):
		
		uri = urlparse.urljoin(self.__class__.API_ROOT, resource.uri)
		
		response = urllib2.urlopen(urllib2.Request(uri))
		return resource.response.from_xml(etree.fromstring(response.read()))
		
	def get_player(self, id=None, steamid=None):
		
		if id is not None:
			return self.request(Player(id=id))
		
		elif steamid is not None:
			return self.request(Player(steamid=steamid))
		
		raise TypeError("No player id or steamid given")
		
