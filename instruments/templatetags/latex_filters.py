import re
import html
import unicodedata
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

register = template.Library()

LATEX_SPECIAL_CHARS = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
    '\\': r'\textbackslash{}',
    '’': "'",
    '‘': "'",
    '“': "``",
    '”': "''",
    '´': "'",  # acute
    '`': "'",  # grave
    '\xa0': '~',  # non-breaking space
    '–': '--',  # en-dash
    '—': '---',  # em-dash
    '…': r'\ldots{}',  # ellipsis
    '€': r'\euro{}',  # optional LaTeX package
    '£': r'\pounds{}',
}


@register.filter(name="latex_escape", is_safe=True, needs_autoescape=True)
def latex_escape(value, autoescape=True):
    if autoescape:
        value = conditional_escape(value)

    # Stap 1: HTML-entiteiten naar echte tekens
    value = html.unescape(str(value))
    value = unicodedata.normalize("NFKC", value)
    value = ''.join(c for c in value if unicodedata.category(c) != "Cf")

    # Stap 2: LaTeX-speciale tekens escapen
    result = re.sub(
        r'([&%$#_{}~^\\])',
        lambda match: LATEX_SPECIAL_CHARS.get(match.group(0), match.group(0)),
        value,
    )
    return mark_safe(result)










# import re
# from django import template
# from django.utils.safestring import mark_safe
# from django.utils.html import conditional_escape
# import html
# import unicodedata

# register = template.Library()

# LATEX_SPECIAL_CHARS = {
#     '&': r'\&',
#     '%': r'\%',
#     '$': r'\$',
#     '#': r'\#',
#     '_': r'\_',
#     '{': r'\{',
#     '}': r'\}',
#     '~': r'\textasciitilde{}',
#     '^': r'\textasciicircum{}',
#     '\\': r'\textbackslash{}',
#     '’': "'",
#     '‘': "'",
#     '“': "``",
#     '”': "''",
#     '´': "'",  # acute
#     '`': "'",  # grave
#     '\xa0': '~',  # non-breaking space
#     '–': '--',  # en-dash
#     '—': '---',  # em-dash
#     '…': r'\ldots{}',  # ellipsis
#     '€': r'\euro{}',  # optional LaTeX package
#     '£': r'\pounds{}',
# }

# @register.filter(name="latex_escape", is_safe=True, needs_autoescape=True)
# def latex_escape(text):
#     """Escapes LaTeX-speciale tekens op veilige manier."""
#     if not isinstance(text, str):
#         return text

#     # 1. HTML-entiteiten unescapen
#     text = html.unescape(text)

#     # 2. Unicode normalisatie (vervang bijv. gecombineerde accenten)
#     text = unicodedata.normalize("NFKC", text)

#     # 3. Escape LaTeX-speciale karakters
#     return ''.join(LATEX_SPECIAL_CHARS.get(char, char) for char in text)