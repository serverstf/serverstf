
from django.core.management.base import BaseCommand, CommandError

from browser.models import Server

import optparse
import urllib
import gzip
import StringIO
import os

from browser.settings import GEOIP_CITY_DATA

class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
					optparse.make_option("--source",
						action="store",
						type="str",
						dest="source",
						default="http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz",
						help="URI of the gzipped GeoIP (City) database"
						),
					optparse.make_option("--skipdl",
						action="store_true",
						dest="skip_download",
						default=False,
						help="Skip downloading fresh GeoIP DB; is ignored when no DB already present"
						),
					)
					
	def handle(self, *args, **kwargs):
		
		if not os.path.isfile(GEOIP_CITY_DATA) or not kwargs["skip_download"]:
			self.stdout.write("Downloading DB from {}".format(kwargs["source"]))
			archive_data = StringIO.StringIO(urllib.urlopen(kwargs["source"]).read())
		
			with open(GEOIP_CITY_DATA, "wb") as geoipdb:
				with gzip.GzipFile(fileobj=archive_data) as gzip_file:
					geoipdb.write(gzip_file.read())
		
		for i, sv in enumerate(Server.objects.all()):
			sv.update_geoip()
			if i % 250 == 0:
				self.stdout.write("  {:>6}".format(i))
		self.stdout.write("  {:>6}".format(i))
