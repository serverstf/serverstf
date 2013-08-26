
class Modal(object):
	
	
	def __init__(self, request):
		
		self.name = self.__class__.name
		self.title = self.__class__.title
		self.icon = self.__class__.icon
		
		self.content = self.__class__.get_content(request)
