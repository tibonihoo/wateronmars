# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2013 Thibauld Nion
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
from wom_pebbles.models import URL_MAX_LENGTH


class WebFeed(models.Model):
  """Represent a web feed (typically RSS or Atom) associated to a
  reference to be considered as a source of news items.
  """
  # Reference consdiered as the source
  source = models.ForeignKey(Reference)
  # The URL where to get updated list of References from
  xmlURL = models.CharField(max_length=URL_MAX_LENGTH)
  # Date marking the last time the source was checked for an update
  last_update_check = models.DateTimeField('last update')
      
