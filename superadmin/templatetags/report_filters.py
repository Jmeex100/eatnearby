from django import template

register = template.Library()

@register.filter
def dictlookup(value, key):
    if isinstance(value, dict):
        return value.get(key, key)
    return key

@register.filter
def lookup(value, dictionary):
    if isinstance(dictionary, dict):
        return [dict(dictionary).get(item, item) for item in value]
    elif isinstance(dictionary, (list, tuple)):  # Handle list/tuple of tuples
        dict_map = {k: v for k, v in dictionary}
        return [dict_map.get(item, item) for item in value]
    return value