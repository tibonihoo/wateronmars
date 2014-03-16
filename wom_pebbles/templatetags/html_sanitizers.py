#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

DANGEROUS_TAGS_NAMES = "(span|div|script)"
DANGEROUS_TAGS_RE = re.compile("(<{0}\s*/?>|<{0}\s+[^>]+>|</{0}>)"\
                               .format(DANGEROUS_TAGS_NAMES))

def auto_esc(text,autoescape):
  """
  Escape or not (just to factorize a little bit of code).
  """
  if autoescape:
    return conditional_escape(text)
  else:
    return text

@register.filter(needs_autoescape=True)
def defang_html(text, autoescape=None):
  """
  Remove tags mentionned in the space separated list 'tags' given as input.
  """
  soup = BeautifulSoup(auto_esc(text,autoescape))
  for tag in soup.find_all("script"):
    tag.replace_with('')
  html = unicode(soup)
  text = DANGEROUS_TAGS_RE.sub(" ",auto_esc(html,autoescape))
  return mark_safe(text)

