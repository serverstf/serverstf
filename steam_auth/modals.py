
from django.core.urlresolvers import reverse

from serverstf import modal
from steam_auth.forms import SettingsForm

## TODO: MAKE SURE THAT TURNING AUTOESCAPE OFF FOR MODAL CONTENT
## IS NOT A POSSIBEL ATTACK VECTOR

class SettingsModal(modal.Modal):
	
	name = "settings"
	title = "Settings"
	icon = "icon-cogs"
	
	@staticmethod
	def get_content(request):
		
		return "<form action='{}' method='POST'>{}</form>".format(
					reverse("settings.handler"),
					SettingsForm().as_p())
