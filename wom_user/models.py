from django.db import models

from django.contrib.auth.models import User

from wom_classification.models import Tag

from wom_pebbles.models import Source

from wom_river.models import FeedSource


class UserProfile(models.Model):
  """
  Gather user-specific information and settings. 
  """
  # The user of whom this is the profile
  user = models.OneToOneField(User)
  # Tags used by the users for references and sources
  tags  = models.ManyToManyField(Tag)
  # User's selection of sources (including "private" ones)
  sources = models.ManyToManyField(Source)
  # User's selection of syndicated sources (subset of the list of
  # sources and used to ease the feeds update procedure )
  feed_sources = models.ManyToManyField(FeedSource,related_name="+")

  def __unicode__(self):
    return "%s's profile" % self.user
