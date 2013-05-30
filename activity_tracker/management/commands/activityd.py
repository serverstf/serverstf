
import logging
logging.basicConfig(format="%(asctime)s [%(levelname)8s] %(threadName)s/%(name)s %(message)s", level=logging.CRITICAL)

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from browser.models import Server

import time
import threading

class ActivityPoller(threading.Thread):
	
	pollers = []
	
	@classmethod
	def spawn(cls, quantity=1):
		
		for x in xrange(quantity):
			cls().start()
		
	@classmethod
	def assign(cls, task):
		
		while True:
			poller = cls.pollers.pop(0)
			
			if not poller.is_busy:
				poller.task = task
				cls.pollers.append(poller)
				break
				
			cls.pollers.append(poller)
				
	def __new__(cls, *args, **kwargs):
	
		poller = object.__new__(cls, *args, **kwargs)
		cls.pollers.append(poller)
		
		return poller
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.task = None
	
	@property
	def is_busy(self):
		return self.task is not None
	
	def process_task(self):
		
		try:
			self.task.update()
		except AttributeError:
			pass
		
	def run(self):
		
		while True:
			if self.task:
				self.process_task()
				self.task = None

class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
					make_option("--nthreads",
						action="store",
						type="int",
						dest="nthreads",
						default=1,
						help="Number of activity poller threads to spawn"
						),
					)
	
	def handle(self, *args, **options):
		
		self.stdout.write("Spawning {} threads ...".format(options["nthreads"]))
		ActivityPoller.spawn(options["nthreads"])
		
		while True:
			
			t_start_pass = time.time()
			nupdated = 0
			nskipped = 0
			nnew = 0 
			
			self.stdout.write(time.strftime("Started pass at %Y-%m-%d %H:%M:%S", time.gmtime(t_start_pass)))
			for server in Server.objects.all().iterator():
				if server.needs_update:
					self.stdout.write("    Updating {}:{} ({})".format(
														server.host,
														server.port,
														server.name))
					ActivityPoller.assign(server)
					nupdated += 1
				else:
					nskipped += 1
					
			self.stdout.write("Completed pass in {time}; {nup} updates, {nskip} skipped, {nnew} new".format(
											time=time.strftime("%M:%S", time.gmtime(time.time() - t_start_pass)),
											nup=nupdated,
											nskip=nskipped,
											nnew=nnew
											))
