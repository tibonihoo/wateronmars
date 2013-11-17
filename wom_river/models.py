from django.db import models

from wom_pebbles.models import Reference
from wom_pebbles.models import SourceProductionsMapper
from wom_pebbles.models import URL_MAX_LENGTH

from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User


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
      
  def get_source_productions_mapper(self):
    """
    Return the SourceProductionsMapper instance associated with this WebFeed.
    """
    try:
      return SourceProductionsMapper.objects.get(source=self.source)
    except ObjectDoesNotExist:
      spm = SourceProductionsMapper(source=self.source)
      spm.save()
      return spm


class ReferenceUserStatus(models.Model):
  """
  Grossly represents the "unread" flag: if no instance exists for a
  given feed item, then the corresponding reference is unread, as it
  is too if an instance exists zith the read flag set to false, but if
  the read flag is set to true, then the user has read the reference.
  """
  # The reference that waits to be read
  ref = models.ForeignKey(Reference)
  # The user that is supposed to read it
  user = models.ForeignKey(User)
  # Repeat the publication date of the reference
  ref_pub_date = models.DateTimeField('reference publication date')
  # Read flag
  has_been_read = models.BooleanField(default=False)
  # Saved flag
  has_been_saved = models.BooleanField(default=False)

  def __unicode__(self):
    return "'%s' (read: %s, saved: %s by '%s')" \
      % (self.ref.title,self.has_been_read,self.has_been_saved,self.user.username)
