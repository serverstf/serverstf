
from django import forms

from lobby.models import Party, Lobby

class PartyForm(forms.ModelForm):
	
	class Meta:
		model = Party
		fields = ["map", "type", "config"]

class ClassSelectionForm(forms.Form):
	roles = forms.MultipleChoiceField(required=False,
										choices=Lobby.ALL_CLASS_CHOICES,
										widget=forms.SelectMultiple(attrs={"size": 9}))
