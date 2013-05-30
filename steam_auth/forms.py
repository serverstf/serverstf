
from django import forms
from django.core.exceptions import ValidationError

import steam.id

class SteamIDField(forms.CharField):
	
	def to_python(self, value):
		
		try:
			return steam.id.SteamID.from_text(str(value))
		except steam_id.SteamIDError as exc:
			raise ValidationError(str(exc))
	
	def clean(self, value):
		
		value = self.to_python(value)
		self.validate(str(value))
		self.run_validators(str(value))
		
		return value
