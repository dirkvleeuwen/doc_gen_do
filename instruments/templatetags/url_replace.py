from django import template

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    if field == 'sort' and dict_.get('sort') == value:
        # If sorting by the same field, toggle direction
        dict_[field] = value + '_desc'
    elif field == 'sort' and dict_.get('sort') == value + '_desc':
        # If sorting descending, remove sort param to go back to default or ascending
        dict_.pop(field, None)
    else:
        dict_[field] = value
        # Reset page number when changing sort or filters
        if field != 'page':
            dict_.pop('page', None)

    return dict_.urlencode()