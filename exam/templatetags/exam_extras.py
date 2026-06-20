from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Look up a value in a dict by a variable key, from a template."""
    if not dictionary:
        return None
    return dictionary.get(key)
