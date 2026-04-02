from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def adapt_http_to_https(context, url_string):
    """
    Switches 'http://' to 'https://' in the given string if the current 
    request is secure (accessed via HTTPS).
    
    Usage in template: {% adapt_http_to_https request.url %}
    """
    request = context.get('request')
    
    # Safety check: ensure request exists (though usually available if USE_TEMPLATES is on)
    if not request:
        return url_string

    # Check if the current request is secure
    if request.is_secure():
        # Only replace if the string starts with http:// to avoid accidental double replacements
        # or replacing https:// with https:// (which is harmless but inefficient)
        if url_string.startswith('http://'):
            return url_string.replace('http://', 'https://', 1)
    
    return url_string
