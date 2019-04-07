# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2019 Thibauld Nion
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

if hasattr(settings,"WOM_TRIBUTARY_TWITTER_OAUTH_TOKEN"):
  # Only useful in dev mode as a single token is only usable to access 1 user account.
  SINGLE_USER_TWITTER_OAUTH_TOKEN = settings.WOM_TRIBUTARY_TWITTER_OAUTH_TOKEN
else:
  SINGLE_USER_TWITTER_OAUTH_TOKEN = None

if hasattr(settings,"WOM_TRIBUTARY_TWITTER_OAUTH_TOKEN_SECRET"):
  # Only useful in dev mode as a single token is only usable to access 1 user account.
  SINGLE_USER_TWITTER_OAUTH_TOKEN_SECRET = settings.WOM_TRIBUTARY_TWITTER_OAUTH_TOKEN_SECRET
else:
  SINGLE_USER_TWITTER_OAUTH_TOKEN_SECRET = None
