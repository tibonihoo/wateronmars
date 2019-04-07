#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from django import template

register = template.Library()

# This regex is the one for a URI scheme where the name is forced to start
# with "wom-" (see also https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#Definition)
WOM_PROTOCOL_RE = re.compile("^wom-[\w\+\.\-]+:.*")

@register.filter()
def normalize_wom_protocol_url(url):
  """
  When a URL is a "wom" protocol, return a more generally "usable" url.
  """
  if WOM_PROTOCOL_RE.match(url):
      return "#"
  else:
      return url

