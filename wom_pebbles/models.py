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


# Max number of characters in a URL.
# Let's make it long enough to get twice the (not so) good old Windows
# path limit.
# WARNING: READ ONLY !
URL_MAX_LENGTH = 255

# Max number of characters for a reference title.
# Let's make it long enough to get a 140 char tweet plus a little extra.
# WARNING: READ ONLY !
REFERENCE_TITLE_MAX_LENGTH = 150



class Reference(models.Model): # A pebble !
  """
  The most basic item representing a piece of information on the
  internet (aka a bookmark or a newsitem).
  """
  # The URL identifies a reference (and URLs will be used as URIs),
  # but several references may share the same URL especially if they
  # have been published by different sources.
  url = models.CharField(max_length=URL_MAX_LENGTH,unique=True)
  # Title of the reference (compulsory)
  title = models.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH)
  # A short summary about the reference's content.
  # WARNING: this is for a description provided by the author of the
  # reference, visible to everybody. User-specific description should
  # better be stored in another "model".
  description = models.TextField(default="", blank=True)
  # Tells when the reference was first published, as a timezone-aware
  # datetime object.
  pub_date = models.DateTimeField('date published')
  # Count the number of users that saved this reference
  # IMPORTANT: use add_pin instead !
  pin_count = models.IntegerField(default=0)
  # Sources of this reference
  sources = models.ManyToManyField("self",symmetrical=False,related_name="productions")

  def add_pin(self):
    self.pin_count += 1

  def __str__(self):
    return "%s[%s]" % (self.title,self.url)
