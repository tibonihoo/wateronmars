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

from datetime import timedelta, datetime, timezone
from django.db import models

from wom_pebbles.models import Reference
from wom_pebbles.models import URL_MAX_LENGTH

DEFAULT_RELEVANCE_DURATION = timedelta(weeks=4)

class WebFeed(models.Model):
  """Represent a web feed (typically RSS or Atom) associated to a
  reference to be considered as a source of news items.
  """
  # Reference considered as the source
  source = models.ForeignKey(Reference, on_delete=models.CASCADE)
  # The URL where to get updated list of References from
  xmlURL = models.CharField(max_length=URL_MAX_LENGTH)
  # Date marking the last time the source was checked for an update
  last_update_check = models.DateTimeField('last update')
  # Time before considering an item obsolete
  item_relevance_duration = models.DurationField(
      default=DEFAULT_RELEVANCE_DURATION)


DEFAULT_FLUSHED_PUB_DATE = datetime.fromtimestamp(0, tz=timezone.utc)

class WebFeedCollation(models.Model):
  """Collect references from a feed that
  needs to be collated (ie grouped together).

  Note: designed to be used as a buffer where to store the references
  waiting to be collated, qssuming thqt once the references are
  collated the list is cleared.
  """
  # Target feed
  feed = models.ForeignKey(WebFeed, on_delete=models.CASCADE)
  # References to be collated
  references = models.ManyToManyField(Reference)
  # Last time the references were collated
  last_completed_collation_date = models.DateTimeField('latest collation date')
  # Pub date of the latest reference that was part of a flush
  latest_reference_flushed = models.DateTimeField(
      'latest reference flushed',
      default=DEFAULT_FLUSHED_PUB_DATE)

  def flush(self, completion_date):
    self.latest_reference_flushed = max(r.pub_date for r in self.references.all())
    self.references.clear()
    self.last_completed_collation_date = completion_date

  def take(self, reference):
    threshold = self.latest_reference_flushed
    pub_date = reference.pub_date
    if pub_date <= threshold:
        return
    if threshold == DEFAULT_FLUSHED_PUB_DATE:
      # Backward compatibility for before/after addition
      # of the 'latest_reference_flushed attribute'
      if pub_date < self.last_completed_collation_date:
        return
    self.references.add(reference)
