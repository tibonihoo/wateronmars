from django.db import models

from django.contrib.auth.models import User

from wom_pebbles.models import Reference

from wom_river.models import WebFeed


  
class UserProfile(models.Model):
  """
  Gather user-specific information and settings. 
  """
  # The user of whom this is the profile
  user = models.OneToOneField(User)
  # User's selection of syndicated sources
  web_feeds = models.ManyToManyField(WebFeed,related_name="+")
  # User sources (includes the sources related to the web_feeds too !)
  sources = models.ManyToManyField(Reference)
  
  def __unicode__(self):
    return "%s>Profile" % self.user


class UserBookmark(models.Model):
  """This is the "personal" facette of a Reference and may contain
  stuff modified by the user.
  
  There may be as many UserBookmark instances for a same reference as
  there are users...
  """
  owner = models.ForeignKey(User)
  # The saved reference
  # WARNING: note that the Reference class has a save_count that must
  # be incremented when linked by a UserBookmark.
  reference = models.ForeignKey(Reference)
  # Date at which the bookmark was created
  saved_date = models.DateTimeField('saved date')
  # Flag telling if the User accepts the bookmark to be public
  is_public = models.BooleanField(default=False)
  # User-specific note about the reference
  comment = models.TextField(default="")
  
  def __unicode__(self):
    return "%s%s>%s" % (self.owner,"" if self.is_public else "<private",
                        self.reference)

