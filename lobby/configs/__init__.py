
import os
import glob
import inspect

from bases import Config

all_configs = {}

for module in glob.iglob(os.path.dirname(__file__) + "/*.py"):
	
	module_name = os.path.basename(module)[:-3]
	if module_name != "__init__":
		mod = __import__(module_name, globals(), locals(), [], 1)
		
		for name, obj in inspect.getmembers(mod):
			if inspect.isclass(obj):
				if issubclass(obj, Config):
					try:
						all_configs[obj.id] = obj
					except AttributeError:
						# No id attr, probably  a base class, safe to
						# ignore it. This will mean classes were the
						# id has simply been forgotten will also be
						# silently ignored.
						pass
					
class ConfigurationError(Exception): pass

del os
del glob
del inspect
del Config
