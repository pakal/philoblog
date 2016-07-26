from django import template

register = template.Library()

#  Custom tag for diagnostics
@register.simple_tag()
def debug_object_dump(var):
    return vars(var)
