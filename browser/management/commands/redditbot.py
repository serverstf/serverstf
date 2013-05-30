
import re

from django.core.management.base import BaseCommand, CommandError
from browser.models import Server

from serverstf.iso3166 import ISO3166

import optparse
import steam.servers
import praw

ADDRESS_REGEX = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}\b")
COMMENT_TEMPLATE = """[**{name}**]({link})

# {slots} slots, {loc}{tags}
"""
COMMENT_TAIL = "[Please report any issues.](http://www.reddit.com/message/compose/?to=Hollinski)"
COMMENT_TAIL = ""

class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
					optparse.make_option("--username",
						action="store",
						type="str",
						dest="username",
						),
					optparse.make_option("--password",
						action="store",
						type="str",
						dest="password",
						),
					optparse.make_option("--store",
						action="store",
						type="str",
						dest="store"
						),
					)
	
	def handle(self, *args, **kwargs):
		
		reddit = praw.Reddit(user_agent="Servers.tf Bot /u/Hollinski")
		reddit.login(kwargs["username"], kwargs["password"])
		
		processed_posts = set()
		processed_comments = set()
		
		for subreddit_name in args:
			subreddit = reddit.get_subreddit(subreddit_name)
			
			for post in subreddit.get_new(limit=20):
				for comment in praw.helpers.flatten_tree(post.comments):
					
					if comment.id in processed_comments:
						continue
					
					processed_comments.add(comment.id)
					
					if comment.author.name == kwargs["username"]:
						self.stdout.write("{} is own post".format(comment.id))
						continue
					
					if kwargs["username"] in [r.author.name for r in comment.replies]:
						self.stdout.write("{} already responded".format(comment.id))
						continue
						
							
					response = []
					match = ADDRESS_REGEX.findall(comment.body)
					if match:
						for addr in match:

							ip, port = addr.split(":")
							port = int(port)
							
							try:
								sv = Server.objects.get(host=ip, port=port)
							except Server.DoesNotExist:
								sv = Server(
										host=ip,
										port=port
										)
								sv.save()
							
							if sv.needs_update:
								sv.update()
							
							if sv.is_online:
								tags = []
								
								if sv.has_random_crits:
									tags.append("crits")
								if sv.has_bullet_spread:
									tags.append("bullet spread")
								if sv.has_damage_spread:
									tags.append("damage spread")
								if sv.lowgrav:
									tags.append("lowgrav")
								if tags.alltalk_enabled:
									tags.append("alltalk")
								
								response.append(COMMENT_TEMPLATE.format(
													name=sv.name,
													link="steam://connect/{}:{}".format(sv.host, sv.port),
													slots=sv.max_players,
													loc=ISO3166.get(sv.country_code, sv.country_code).lower().title(),
													tags=", " + ",".join(tags)
													))
					#from pprint import pprint
					#pprint(vars(comment.replies))
					#pprint(comment.replies)
					#break
					
					if response:
						self.stdout.write("{} Replied; {} servers".format(comment.id, len(response)))
						comment.reply("\n".join(response + [COMMENT_TAIL]))
						#print "\n".join(response + [COMMENT_TAIL])
						#print
						#print
