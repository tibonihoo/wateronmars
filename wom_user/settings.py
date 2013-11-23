# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

"""
Gather all parameters specific to this application: the default
values and the way to read them from the global django site settings.
"""

from django.conf import settings

from datetime import datetime
from datetime import timedelta
from django.utils import timezone


if hasattr(settings,"WOM_USER_NEWS_TIME_THRESHOLD"):
  NEWS_TIME_THRESHOLD = settings.WOM_USER_NEWS_TIME_THRESHOLD
else:
  NEWS_TIME_THRESHOLD = datetime.now(timezone.utc)-timedelta(weeks=12)

if hasattr(settings,"WOM_USER_MAX_ITEMS_PER_PAGE"):
  MAX_ITEMS_PER_PAGE = settings.WOM_USER_MAX_ITEMS_PER_PAGE
else:
  MAX_ITEMS_PER_PAGE = 100

  
