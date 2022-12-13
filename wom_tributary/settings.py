# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2019 Thibauld Nion
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


"""
Application credentials for twitter can be provided in two ways:

- for "development mode" you can use a single user token and set it in
  the main applications settings (see below how this would then be
  extracted)

- for the "production" application use application key and
  secrets. They must be stored in their own files in the folder where
  the application is run (its current working directory when it runs).
  The files need to be named `twitter_app_key` and `twitter_app_secret`
  and contain the key and secret strings only.
"""

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
