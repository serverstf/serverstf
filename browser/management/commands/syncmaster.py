
from django.core.management.base import BaseCommand, CommandError

from browser.models import Server

import optparse
import steam.servers

class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
					optparse.make_option("--address",
						action="store",
						type="str",
						dest="address",
						default="{}:{}".format(*steam.servers.MASTER_SERVER_ADDR),
						help="Address in form host:port of the Master Server"
						),
					optparse.make_option("--timeout-limit",
						action="store",
						type="int",
						dest="max_timeouts",
						default=5,
						help="Maximum number of times a request for a particular region can timeout before being skipped"
						),
					optparse.make_option("--timeout",
						action="store",
						type="float",
						dest="timeout",
						default=5.0,
						help="Timeout in seconds for each request"
						),
					)
	
	region_names = {
					"all": [
							steam.servers.REGION_AFRICA,
							steam.servers.REGION_ASIA,
							steam.servers.REGION_AUSTRALIA,
							steam.servers.REGION_EUROPE,
							steam.servers.REGION_MIDDLE_EAST,
							steam.servers.REGION_REST,
							steam.servers.REGION_SOUTH_AMERICA,
							steam.servers.REGION_US_EAST_COAST,
							steam.servers.REGION_US_WEST_COAST,
							],
					"eu": [steam.servers.REGION_EUROPE],
					"us": [
							steam.servers.REGION_US_EAST_COAST,
							steam.servers.REGION_US_WEST_COAST
							],
					"useast": [steam.servers.REGION_US_EAST_COAST],
					"uswest": [steam.servers.REGION_US_EAST_COAST],
					"asia": [steam.servers.REGION_ASIA],
					"aus": [steam.servers.REGION_AUSTRALIA],
					"africa": [steam.servers.REGION_AFRICA],
					"middleeast": [steam.servers.REGION_AUSTRALIA],
					"southamerica": [steam.servers.REGION_SOUTH_AMERICA],
					"rest": [steam.servers.REGION_REST]
					}
	
	def handle(self, *args, **kwargs):
		
		regions = set()
		for region_name in args:
			try:
				for region in Command.region_names[region_name]:
					regions.add(region)
			except KeyError:
				raise CommandError("No such region as '{}'".format(region_name))
		
		try:
			msq_host = kwargs["address"].split(":")[0]
			msq_port = int(kwargs["address"].split(":")[-1])
		except ValueError:
			raise CommandError("Invalid Master Server address format; expected {host}:{port}")
			
		msq = steam.servers.MasterServerQuerier((msq_host, msq_port), kwargs["timeout"])
		
		for region in regions:
			region_name = {getattr(steam.servers, n): n for n in dir(steam.servers) if n.startswith("REGION_")}[region]
			self.stdout.write("Requesting server list for {}".format(region_name))
			
			timeout_count = 0
			sv_count = 0
			sv_exists_count = 0
			
			last_addr = "0.0.0.0:0"
			while timeout_count < kwargs["max_timeouts"]:
				try:
					for sv_addr in msq.get_region(region, filter=r"\gamedir\tf", last_addr=last_addr):
						
						try:
							Server.objects.get(host=sv_addr[0], port=sv_addr[1])
							sv_exists_count += 1
						except Server.DoesNotExist:
							svr = Server(
									host=sv_addr[0],
									port=sv_addr[1]
									)
							svr.update()
							svr.save()
						
						sv_count += 1
						if sv_count % 250 == 0:
							self.stdout.write("  {:>6}".format(sv_count))
				except steam.servers.NoResponseError as exc:
					self.stderr.write("  Request timedout")
					#timeout_count += 1
					#last_addr = exc.args[1]
					#continue
					
					# TODO: add support for get_region 'continues' in
					# steam.servers.
					
					timeout_count = kwargs["max_timeouts"]
					continue
					
				break
				
			self.stdout.write("  {:>6} servers processed; {} new".format(sv_count, sv_count - sv_exists_count))
