
import inspect

from django.conf import settings

from serverstf import modal
from pprint import pprint

def context_modals(request):
	
	modal_names = set()
	modals = []

	for app_name in ["steam_auth"]:
		app_name += ".modals"
		
		app = __import__(app_name)
		for name, member in inspect.getmembers(app.modals):
			if inspect.isclass(member):
				if issubclass(member, modal.Modal):
					if member.name in modal_names:
						raise KeyError("Conflicting names '{}'".format(member.name))
					
					modal_names.add(member.name)
					modals.append(member(request))
		
	return {"modals": modals}
