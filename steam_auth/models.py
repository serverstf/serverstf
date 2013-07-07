
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError

from browser.models import Server
from serverstf.iso3166 import CONTINENT_CHOICES
from steam_auth.settings import STEAM_API_KEY

from celery.contrib.methods import task

import datetime

import steam.id
import steam.api
import steam_auth.forms

steam_api = steam.api.SteamAPI(STEAM_API_KEY)

class SteamIDField(models.CharField):
	
	__metaclass__ = models.SubfieldBase
	description = "A textual SteamID (STEAM_X:Y:Z)"
	
	def __init__(self, *args, **kwargs):
		kwargs["max_length"] = 22
		models.CharField.__init__(self, *args, **kwargs)
		
		# Theoretical max length in form STEAM_X:Y:Z is 22
		# STEAM_255:0:4294967295
	
	def __unicode__(self):
		return unicode(self)
	
	def to_python(self, value):
		
		if isinstance(value, steam.id.SteamID):
			return value
		
		try:
			return steam.id.SteamID.from_text(value)
		except steam_id.SteamIDError as exc:
			raise ValidationError(str(exc))
	
	def get_prep_value(self, value):
		return str(value)
		
	def formfield(self, **kwargs):
		defaults = {'max_length': self.max_length}
		defaults.update(kwargs)
		return steam_auth.forms.SteamIDField(**defaults)
	
	def clean(self, value, model_instance):
		# Coerce to string before handing off to CharField's validators
		
		value = self.to_python(value)
		self.validate(str(value), model_instance)
		self.run_validators(str(value))
		
		return value
	
class UserManager(BaseUserManager):
	
	def create_user(self, steam_id):
		
		user = self.model(steam_id=steam_id)
		user.set_unusable_password()
		user.save(using=self._db)
		
		return user
		
	def create_superuser(self, steam_id, password):
		
		user = self.model(steam_id=steam_id)
		user.set_password(password)
		user.is_admin = True
		user.save(using=self._db)
		
		return user

class User(AbstractBaseUser):
	
	profile_name = models.CharField(max_length=32, default="")
	steam_id = SteamIDField(unique=True, editable=False)
	last_sync = models.DateTimeField(default=datetime.datetime.fromtimestamp(0.0)) 
	favourites = models.ManyToManyField(Server)
	region = models.CharField(max_length=2, null=True, blank=True,
									choices=CONTINENT_CHOICES)
	
	is_admin = models.BooleanField(default=False)
	
	USERNAME_FIELD = "steam_id"
	REQUIRED_FIELDS = []
	
	objects = UserManager()
	
	def __unicode__(self):
		return unicode(self.steam_id)
	
	def get_short_name(self):
		if self.profile_name:
			return self.profile_name
		
		return str(self.steam_id)
		
	def get_long_name(self):
		return self.get_short_name()
	
	def has_perm(self, perm, obj=None):
		
		if self.is_admin:
			return True
		else:
			return False
	
	def has_module_perms(self, app_label):
		
		if self.is_admin:
			return True
		else:
			return False
	
	@property
	def is_staff(self):
		return self.is_admin
	
	@task()
	def syncronise(self):

		player_summary = steam_api.user.get_player_summaries(
							steamids=int(self.steam_id))["response"]["players"][0]
		
		self.profile_name = player_summary["personaname"]
		self.last_sync = datetime.datetime.now()
		
		self.save()
	
## South support
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^steam_auth\.models\.SteamIDField"])
