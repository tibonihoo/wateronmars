# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2013-2019 Thibauld Nion
#
# This file is part of WaterOnMars (https://github.com/tibonihoo/wateronmars) 
#
# WaterOnMars is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# WaterOnMars is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with WaterOnMars.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Gather all parameters specific to this application: the default
values and the way to read them from the global django site settings.
"""

from django.conf import settings

from datetime import timedelta

if hasattr(settings, "WOM_WEB_FEED_COLLATION_MIN_NUM_REF_TARGET"):
  WEB_FEED_COLLATION_MIN_NUM_REF_TARGET = settings.WOM_WEB_FEED_COLLATION_MIN_NUM_REF_TARGET
else:
  WEB_FEED_COLLATION_MIN_NUM_REF_TARGET = 3

if hasattr(settings, "WOM_WEB_FEED_COLLATION_MAX_NUM_REF_TARGET"):
  WEB_FEED_COLLATION_MAX_NUM_REF_TARGET = settings.WOM_WEB_FEED_COLLATION_MAX_NUM_REF_TARGET
else:
  WEB_FEED_COLLATION_MAX_NUM_REF_TARGET = 10

if hasattr(settings,"WOM_WEB_FEED_COLLATION_TIMEOUT"):
  WEB_FEED_COLLATION_TIMEOUT = settings.WOM_WEB_FEED_COLLATION_TIMEOUT
else:
  WEB_FEED_COLLATION_TIMEOUT = timedelta(days=1)

if hasattr(settings,"WOM_USER_MAX_ITEMS_PER_PAGE"):
  MAX_ITEMS_PER_PAGE = settings.WOM_USER_MAX_ITEMS_PER_PAGE
else:
  MAX_ITEMS_PER_PAGE = 100

if hasattr(settings,"WOM_USER_HUMANS_TEAM"):
  HUMANS_TEAM = settings.WOM_USER_HUMANS_TEAM
else:
  HUMANS_TEAM = ""
  
if hasattr(settings,"WOM_USER_HUMANS_THANKS"):
  HUMANS_THANKS = settings.WOM_USER_HUMANS_THANKS
else:
  HUMANS_THANKS = """/* THANKS */
  RSS Hero: Dave Winer.
  Site: http://davewiner.com/

  Feed & Freedom Hero: Aaron Swartz
  Site: http://www.aaronsw.com

  feedparser and feedfinder Creator: Mark Pilgrim
  Site: https://en.wikipedia.org/wiki/Mark_Pilgrim(software_developer)
"""


if hasattr(settings,"WOM_ROOT_URL"):
  ROOT_URL = settings.WOM_ROOT_URL
else:
  raise Exception("'WOM_ROOT_URL' must be provided in the settings.")
