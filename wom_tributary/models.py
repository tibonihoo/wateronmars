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

from datetime import timedelta
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
  source = models.ForeignKey(Reference, on_delete=models.CASCADE)
  
  # Date marking the last time the source was checked for an update
  last_update_check = models.DateTimeField('last update')

  # Time before considering an item obsolete
  item_relevance_duration = models.DurationField(default=timedelta(days=2))


# Consider renaming to TwitterUserAccessInfo
# see for instance: https://stackoverflow.com/questions/2862979/easiest-way-to-rename-a-model-using-django-south
class TwitterUserInfo(models.Model):
  """The oauth tokens that can be used to access twitter API after a user has granted us permission.
  """
  USERNAME_MAX_LENGTH = 50 # Twitter currently says 15 actually
  # User for which these tweets should be looked up
  username = models.CharField(max_length=USERNAME_MAX_LENGTH)
  oauth_access_token = models.TextField()
  oauth_access_token_secret = models.TextField()


class TwitterTimeline(models.Model):
  """Define the twitter timeline to collect and convert to a stream.
  """
  
  SOURCE_URL = "https://twitter.com"
  SOURCE_NAME = "Twitter"
  
  generated_feed = models.OneToOneField(GeneratedFeed, on_delete=models.CASCADE)
    
  # User for which these tweets should be looked up
  # NOTE: in current use case this user will be requested to
  # "authorize" the app, so there may be 'constraints'
  # on what the username can be.
  username = models.CharField(max_length=TwitterUserInfo.USERNAME_MAX_LENGTH)

  # Credential to access twitter (bound to each timeline
  # to be sure we don't fill a timeline while benefiting
  # from credentials of another user)
  twitter_user_access_info = models.ForeignKey(TwitterUserInfo,
                                                 on_delete=models.CASCADE)


