from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Ritorna la querystring corrente (es. '?status=OPEN&page=2'), con eventuali override.
    Uso:
      {% url_replace %}                -> query attuale
      {% url_replace page=1 %}         -> forza page=1
      {% url_replace status=None %}    -> rimuove 'status' se presente
    """
    request = context.get("request")
    if not request:
        return ""
    query = request.GET.copy()

    # override/cleanup da kwargs
    for k, v in kwargs.items():
        if v is None:
            query.pop(k, None)
        else:
            query[k] = v

    encoded = query.urlencode()
    return f"?{encoded}" if encoded else ""
