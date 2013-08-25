
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from steam_auth.decorators import sync
from lobby.models import Lobby, Party
from lobby.forms import PartyForm, ClassSelectionForm

@login_required
@sync
def main(request):
	
	try:
		party = request.user.party_set.all()[0]
	except IndexError:
		party = Party(members=[request.user])
		party.save()
	
	#party = None
	template = loader.get_template("lobby/lobby.html")
	context = RequestContext(request, {
							"party": party,
							"party_form": PartyForm(instance=party),
							"class_form": ClassSelectionForm,
							})
	
	return HttpResponse(template.render(context))

def create(request): return HttpResponse("lol nope")
def join_party(request): return HttpResponse("lol k")
