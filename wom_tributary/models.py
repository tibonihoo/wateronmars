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

from django.db import models

from wom_pebbles.models import Reference


class GeneratedFeed(models.Model):
  """Proxy to a feeds that required extra processing (ypically because
  they come from something else than a web feed).
"""

  TITLE_MAX_LENGTH = 50
  PROVIDER_MAX_LENGTH = 4
  TWITTER = "TWTR"

  PROVIDERS_CHOICE = (
    (TWITTER, "twitter"),
    )
    
  provider = models.CharField(
      max_length=PROVIDER_MAX_LENGTH,
      choices=PROVIDERS_CHOICE,
      default=TWITTER,
    )

  title = models.CharField(
    max_length=TITLE_MAX_LENGTH
    )
  
  # Reference considered as the source
  source = models.ForeignKey(Reference)
  
  # Date marking the last time the source was checked for an update
  last_update_check = models.DateTimeField('last update')
  
  

class TwitterTimeline(models.Model):
  """Define the twitter timeline to collect and convert to a stream.
  """
  
  # Constants
  KIND_MAX_LENGTH = 4
  HOME_TIMELINE = 'HOME'
  USER_TIMELINE = 'USER'
  MENTIONS_TIMELINE = 'MNTN'
  USERNAME_MAX_LENGTH = 50 # Twitter currently says 15 actually
  SOURCE_URL = "https://twitter.com"
  SOURCE_NAME = "Twitter"
  
  KIND_CHOICES = (
    (HOME_TIMELINE, 'HOME_TIMELINE'),
    (USER_TIMELINE, 'USER_TIMELINE'),
    (MENTIONS_TIMELINE, 'MENTIONS_TIMELINE'),
    )

  generated_feed = models.OneToOneField(GeneratedFeed)
  
  # What kind of content to extract
  kind = models.CharField(
    max_length=KIND_MAX_LENGTH,
    choices=KIND_CHOICES,
    default=HOME_TIMELINE,
    )
  
  # User for which these tweets should be looked up
  # NOTE: in current use case this user will be requested to
  # "authorize" the app, so there may be 'constraints' on what the
  # username can be.
  username = models.CharField(max_length=USERNAME_MAX_LENGTH)

