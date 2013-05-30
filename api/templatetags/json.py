
import time

from django import template

register = template.Library()

@register.simple_tag
def join_attrs(iterable, attr_name, dilem):
	return dilem.join((unicode(getattr(o, attr_name)) for o in iterable))

@register.filter
def timestamp(dt):
	return time.mktime(dt.timetuple())

@register.filter
def get_item(dict_, key):
    return dict_.get(key)
