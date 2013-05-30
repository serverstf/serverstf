
from django import template
from django.template.defaultfilters import stringfilter

import serverstf.iso3166

register = template.Library()

@register.filter
@stringfilter
def continent(value):
    return serverstf.iso3166.CONTINENTS.get(value.upper(), "Unknown").title()

@register.filter
@stringfilter
def country(value):
    return serverstf.iso3166.ISO3166.get(value.upper(), "Unknown").title()
