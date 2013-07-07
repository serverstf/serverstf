
from django import forms
from browser.models import Network

class NetworkForm(forms.ModelForm):
	
	class Meta:
		
		model = Network
		fields = ["name", "url", "steam_group", "admins"]
