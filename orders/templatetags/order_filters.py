from django import template

register = template.Library()

@register.filter
def to_dict(choices):
    """Convert choices list to dict"""
    if isinstance(choices, list):
        return dict(choices)
    return {}

@register.filter
def get(value, arg):
    """Get item from dict"""
    return value.get(arg, '')
