from django import template

register = template.Library()

@register.inclusion_tag('instruments/partials/floating_field.html')
def render_floating(field):
    return {'field': field}