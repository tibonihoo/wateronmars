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

from django.db import models

from django.contrib.auth.models import User

from wom_pebbles.models import Reference

from wom_river.models import WebFeed, WebFeedCollation

from wom_classification.models import get_item_tag_names

from wom_tributary.models import GeneratedFeed
from wom_tributary.models import TwitterUserInfo
from wom_tributary.models import MastodonUserAccessInfo

class UserProfile(models.Model):
  """
  Gather user-specific information and settings. 
  """
  # The user of whom this is the profile
  owner = models.OneToOneField(User, on_delete=models.CASCADE)
  # User's selection of syndicated sources
  web_feeds = models.ManyToManyField(WebFeed)
  # Feeds that must be collated
  collating_feeds = models.ManyToManyField(WebFeedCollation)
  # All (public+private) sources of user bookmarks
  sources = models.ManyToManyField(Reference,related_name="userprofile")
  # Public sources of a user bookmarks and web_feeds
  public_sources = models.ManyToManyField(Reference,related_name="publicly_related_userprofile")
  # Feeds providing anything else than the plain content of "simple" web feed
  generated_feeds = models.ManyToManyField(GeneratedFeed,related_name="userprofile")
  # Info related to the user's twitter account
  twitter_info = models.OneToOneField(TwitterUserInfo, related_name="userprofile", null=True, on_delete=models.CASCADE)
  
  def __str__(self):
    return "%s>Profile" % self.owner


class UserBookmark(models.Model):
  """This is the "personal" facette of a Reference and may contain
  stuff modified by the user.
  
  There may be as many UserBookmark instances for a same reference as
  there are users...
  """
  owner = models.ForeignKey(User, on_delete=models.CASCADE)
  # The saved reference (WARNING: it must be explicitly added an extra 'pin'
  # when linked by a UserBookmark)
  reference = models.ForeignKey(Reference, on_delete=models.CASCADE)
  # Date at which the bookmark was created
  saved_date = models.DateTimeField('saved date')
  # Flag telling if the User accepts the bookmark to be public
  is_public = models.BooleanField(default=False)
  # User-specific note about the reference
  comment = models.TextField(default="", blank=True)
  
  def __str__(self):
    return "%s%s>%s" % (self.owner,"" if self.is_public else "<private",
                        self.reference)

  def get_public_sources(self):
    """Get the sources of the reference that are also known to the user and publicly visible."""
    return self.reference.sources.filter(publicly_related_userprofile=self.owner.userprofile).all()

  def get_sources(self):
    """Get the sources of the reference that are also known to the user and privately visible."""
    return self.reference.sources.filter(userprofile=self.owner.userprofile).all()

  def get_tag_names(self):
    """Get the names of the tags related to this reference."""
    return [t for t in get_item_tag_names(self.owner,self.reference) if t.strip()]

  def set_private(self):
    """Set the bookmark as private."""
    if not self.is_public: return
    self.is_public = False
    # Check if the corresponding source should be made private, the
    # method is a bit heavy here, which is not so critical because the
    # usual workflow is more private -> public than the opposite
    owner_profile = self.owner.userprofile
    for src in self.reference.sources\
                             .filter(publicly_related_userprofile\
                                     =owner_profile):
      if not src.productions.filter(userbookmark__owner=self.owner,
                                    userbookmark__is_public=True).exists():
        if owner_profile.web_feeds.filter(source=src).exists():
          # Sources related to web feed remain public
          continue
        owner_profile.public_sources.remove(src)
    self.save()
    
  def set_public(self):
    """Set the bookmark as public."""
    if self.is_public: return
    self.is_public = True
    owner_profile = self.owner.userprofile
    for src in self.reference.sources\
                             .filter(userprofile=owner_profile):
      owner_profile.public_sources.add(src)
    self.save()
    
    
class ReferenceUserStatus(models.Model):
  """
  Mainly represents the "unread" flag: if no instance exists for a
  given feed item, then the corresponding reference is unread, as it
  is too if an instance exists with the read flag set to false, but if
  the read flag is set to true, then the user has read the reference.
  """
  # The reference that waits to be read
  reference = models.ForeignKey(Reference, on_delete=models.CASCADE)
  # The user that is supposed to read it
  owner = models.ForeignKey(User, on_delete=models.CASCADE)
  # Repeat the publication date of the reference
  reference_pub_date = models.DateTimeField('reference publication date')
  # Read flag
  has_been_read = models.BooleanField(default=False)
  # Saved flag
  has_been_saved = models.BooleanField(default=False)
  # The main source (used to ease display)
  main_source = models.ForeignKey(Reference,related_name="+", on_delete=models.CASCADE)
  
  
  def __str__(self):
    return "'%s' (read: %s, saved: %s by '%s')" \
      % (self.reference.title,self.has_been_read,self.has_been_saved,self.owner.username)
  
  def get_tag_names(self):
    """Get the names of the tags related to this reference."""
    return get_item_tag_names(self.owner,self.reference)
