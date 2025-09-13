from django import template
register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Mantiene la query string corrente e sostituisce/aggiunge i parametri passati.
    Esempio: {% url_replace page=2 %}
    """
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is None:
            query.pop(k, None)
        else:
            query[k] = v
    qs = query.urlencode()
    return f"?{qs}" if qs else "?"
