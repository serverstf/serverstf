
from django import forms
from django.core.exceptions import ValidationError

import steam.id

from serverstf.iso3166 import CONTINENTS

class SteamIDField(forms.CharField):
	
	def to_python(self, value):
		
		try:
			return steam.id.SteamID.from_text(str(value))
		except steam.id.SteamIDError as exc:
			raise ValidationError(str(exc))
	
	def clean(self, value):
		
		value = self.to_python(value)
		self.validate(str(value))
		self.run_validators(str(value))
		
		return value

class SettingsForm(forms.Form):
	
	default_region = forms.ChoiceField(choices=CONTINENTS.items())
