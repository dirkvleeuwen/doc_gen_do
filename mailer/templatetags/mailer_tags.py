from django import template

register = template.Library()

@register.filter
def display_name(user):
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    if user.initials and user.last_name:
        return f"{user.initials} {user.last_name}"
    return user.email