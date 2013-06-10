from django.db import models

from django.contrib.auth.models import User

from wom_classification.models import Tag

from wom_pebbles.models import Source
from wom_pebbles.models import Reference

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
  # TODO: add registration date or look if Django's user model as one already
  # OK there is one already in User !
  def __unicode__(self):
    return "%s's profile" % self.user


class UserBookmark(models.Model):
  """
  This is the "personal" facette of a Reference and may contain stuff modified by the user.
  There may be as many UserBookmark instances for a same reference as there are users...
  """
  owner = models.ForeignKey(User)
  # The saved reference
  # WARNING: note that the Reference class has a save_count that must
  # be incremented when linked by a UserBookmark.
  reference = models.ForeignKey(Reference)
  # Tags used (at least) for user-explicit classification  
  tags  = models.ManyToManyField(Tag)  
  # Date at which the bookmark was created
  saved_date = models.DateTimeField('saved date')
  # Indicate wether this bookmark may be shared and displayed publicly
  is_public = models.BooleanField(default=False)


