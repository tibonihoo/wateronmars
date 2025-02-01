#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from html_sanitizer.sanitizer import (
    Sanitizer,
    sanitize_href,
    bold_span_to_strong,
    italic_span_to_em,
    tag_replacer,
    target_blank_noopener
    )

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

SANITIZATION_SETTINGS = {
    "tags": {
        "a", "h1", "h2", "h3", "strong", "em", "p", "ul", "ol",
        "li", "br", "sub", "sup", "hr", "img", "b", "i"
    },
    "attributes": {"a": ("href", "name", "target", "title", "id", "rel"),
                   "img": ("src", "alt")
                   },
    "empty": {"hr", "a", "br", "img"},
    "separate": {"a", "p", "li", "img"},
    "whitespace": {"br"},
    "keep_typographic_whitespace": False,
    "add_nofollow": False,
    "autolink": False,
    "sanitize_href": sanitize_href,
    "element_preprocessors": [
        # convert span elements into em/strong if a matching style rule
        # has been found. strong has precedence, strong & em at the same
        # time is not supported
        bold_span_to_strong,
        italic_span_to_em,
        tag_replacer("form", "p"),
        target_blank_noopener,
    ],
    "element_postprocessors": [],
    "is_mergeable": lambda e1, e2: True,
}

@register.filter(needs_autoescape=False)
def defang_html(text):
  """
  Remove tags mentionned in the space separated list 'tags' given as input.
  """
  sanitizer = Sanitizer(settings=SANITIZATION_SETTINGS)
  text_sanitized = sanitizer.sanitize(text)
  return mark_safe(text_sanitized)

