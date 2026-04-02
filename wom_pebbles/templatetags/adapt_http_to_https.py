from django import template


register = template.Library()

@register.filter
def adapt_http_to_https(url_string, request):
    """
    Switches 'http://' to 'https://' in the given string if the request is secure.
    
    Usage in template: {{ url_string|force_https:request }}
    """
    if not url_string:
        return url_string
    
    # Check if request is provided and secure
    if request and hasattr(request, 'is_secure') and request.is_secure():
        if url_string.startswith('http://'):
            return url_string.replace('http://', 'https://', 1)
    
    return url_string
