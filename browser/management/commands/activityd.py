
import logging
log = logging.getLogger(__name__)

from django import db
from django.core.management.base import BaseCommand, CommandError

from browser.models import Server, ActivityLog

from optparse import make_option
import time
import datetime
import threading

class ActivityPoller(threading.Thread):
	"""
		Implements a pool threading system of server activity pollers
		which record player/bot counts for each server at a given time.
		
		Threads are automatically added to the pool when spawned and will
		busy wait until a task is assigned to them.
		
		The internal list of threads requires that lock (Activity._lock)
		be acquired before accessing.
	"""
	
	_lock = threading.Lock()
	pollers = []
	
	@classmethod
	def spawn(cls, quantity=1):
		"""
			Add `quantity` number of pollers to the pool. Will lock.
		"""
		
		for x in xrange(quantity):
			cls().start()
	
	@classmethod
	def join_all(cls):
		"""
			Sends stop signal to all pollers and then joins each poller
			thread, blocking until they all finish. Will lock.
		"""
		
		with cls._lock:
			for poller in cls.pollers:
				poller.stop = True
				
			for poller in cls.pollers:
				poller.join()
	
	@classmethod
	def assign(cls, task):
		"""
			Assign a task to a free thread. Blocks until free thread can
			be acquired. Will lock.
		"""
		
		while True:
			with cls._lock:
				poller = cls.pollers.pop(0)
				
				if not poller.is_busy:
					poller.task = task
					cls.pollers.append(poller)
					break
					
				cls.pollers.append(poller)
			time.sleep(0.1)
			
	def __new__(cls, *args, **kwargs):
		
		with cls._lock:
			poller = object.__new__(cls, *args, **kwargs)
			cls.pollers.append(poller)
		
		return poller
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.task = None
		self.stop = False
	
	@property
	def is_busy(self):
		return self.task is not None
	
	def log_activity(self):
		
		log.debug("Logging {}".format(self.task))
		while True:
			try:
				self.task.update(force=True)
			except db.DatabaseError:
				time.sleep(0.1)
				continue
			except:
				#print "HOST: " + self.task.host
				#print "PORT: " + str(self.task.port)
				raise
					
			break
				
		al = ActivityLog.from_server(self.task)
		while True:
			try:
				al.save()
				break
			except:
				time.sleep(0.1)
			
	def process_task(self):
		
		try:
			latest_al = ActivityLog.objects.filter(server=self.task).latest(field_name="timestamp")
			if datetime.datetime.now() >= latest_al.timestamp + datetime.timedelta(minutes=30):
				self.log_activity()
			else:
				log.debug("Skipping {}".format(self.task))
		except ActivityLog.DoesNotExist:
			# First time being tracked so no ActivityLog exists
			self.log_activity()
		
	def run(self):
		
		# TODO: Don't busy wait
		while not self.stop:
			if self.task:
				self.process_task()
				self.task = None
				
			time.sleep(0.1)

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
		
		ActivityPoller.spawn(options["nthreads"])
		self.stdout.write("Spawning {} threads ...".format(options["nthreads"]))
		
		running = True
		while running:
			
			try:
				count = 0
				t_start = time.time()
				for server in Server.objects.all().iterator():
					ActivityPoller.assign(server)
					count += 1
				#time.sleep(5 * 60)
				self.stdout.write("Processed {} servers in {} minutes {}".format(
										count,
										int((time.time() - t_start) / 60),
										"(WARNING)" if (time.time() - t_start) > 3600 else ""
										))
				db.reset_queries()
			except KeyboardInterrupt:
				running = False
				
		self.stdout.write("Waiting for pollers to finish ...")	
		ActivityPoller.join_all()
