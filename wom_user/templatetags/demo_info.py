#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings

from django import template

register = template.Library()



def demo_info():
  """
  Render a message with info about the demo mode.
  """
  return {
    'is_in_demo': settings.DEMO,
    'is_read_only': settings.READ_ONLY,
    'demo_u_name': settings.DEMO_USER_NAME,
    'demo_u_password': settings.DEMO_USER_PASSWD,
  }

# Register the custom tag as an inclusion tag with takes_context=True.
register.inclusion_tag('demo_info.html')(demo_info)

