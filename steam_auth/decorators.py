
def sync(view):
	"""
		Synchronises the user's profile with their Steam profile.
		
		If user is not authenticated then no operation occurs. Note that
		synchronisation is asynchronous.
	"""
	
	def wrap(request, *args, **kwargs):
		
		if request.user.is_authenticated():
			request.user.synchronise()
		
		return view(request, *args, **kwargs)
		
	return wrap
