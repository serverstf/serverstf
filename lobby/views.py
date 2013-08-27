
from django.shortcuts import redirect
from django.http import HttpResponse, Http404
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
		party = Party.objects.create(members=[request.user])
		party.save()
	
	template = loader.get_template("lobby/lobby.html")
	context = RequestContext(request, {
							"party": party,
							"party_form": PartyForm(instance=party),
							"class_form":ClassSelectionForm,
							})
	
	return HttpResponse(template.render(context))

def create(request): return HttpResponse("lol nope")

@login_required
def join_party(request, id):
	
	try:
		party = Party.objects.get(id=int(id))
	except Party.DoesNotExist:
		return redirect("lobby.main")
		
	request.user.party_set.remove(request.user)
	party.members.add(request.user)
	
	return redirect("lobby.main")

## REST interfaces
from rest_framework import response
from rest_framework import viewsets

from lobby.serialisers import PartySerialiser

class PartyViewSet(viewsets.ViewSet):
	
	def retrieve(self, request, pk):
		
		try:
			party = Party.objects.get(pk=pk)
		except Party.DoesNotExist:
			raise Http404
		
		return response.Response(PartySerialiser(party).data)
