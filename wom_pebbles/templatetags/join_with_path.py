from django import template


register = template.Library()

@register.filter
def join_with_path(url_string, sub_path):
    """
    Join the two paths, taking care of ending and leading "/" to avoid duplicates.
    
    Usage in template: {{ url_string|join_with_path:sub_path }}
    """
    clean_url_string = url_string.rstrip("/")
    clean_sub_path = sub_path.lstrip("/")
    return "/".join((clean_url_string, clean_sub_path))
