
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from lobby import tasks
from lobby.models import Lobby
import lobby.configs as configs

class Command(BaseCommand):
	# Only ever have one instance of this command running at a time,
	# otherwise issues will arise from having multiple tasks trying
	# to update a single lobby.
	
	option_list = BaseCommand.option_list + (
					)
	
	def handle(self, *args, **options):

		active_tasks = {}
		state_task_map = {
			Lobby.CREATED: tasks.configure,
			#Lobby.CONFIGURED: tasks.start,
			#Lobby.STARTED: tasks.check_players,
			#Lobby.IN_PROGRESS: tasks.check_finished,
			#Lobby.FINISHED: tasks.revert,
			}
		
		#while True:

		for lobby in Lobby.objects.exclude(state=Lobby.COMPLETE):
			
			task = state_task_map[lobby.state]
			if task is not None and lobby.id not in active_tasks:
				active_tasks[lobby.id] = task.apply_async([lobby.id])
				
		for lobby_id, task in active_tasks.iteritems():
			if task.ready():
				del active_tasks[lobby_id]
				# Free the lobby to move onto the next task. Assumes that
				# the task has progressed the state
				
				# NOTE: If the a task doesn't advance the state of the
				# lobby this may result in infinite loops with hte task
				# being tried over and over again. In production, if the 
				# task fails forw hatever reason, the state should be set 
				# to COMPLETE
