
from django import forms
from iso3166 import CONTINENTS

class SettingsForm(forms.Form):
	
	default_region = forms.ChoiceField(choices=CONTINENTS.items())
	use_static_ui = forms.BooleanField()
