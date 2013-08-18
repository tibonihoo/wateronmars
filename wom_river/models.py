from django.db import models

from wom_pebbles.models import Source
from wom_pebbles.models import URL_MAX_LENGTH

from django.contrib.auth.models import User

from wom_pebbles.models import Reference


class FeedSource(Source):
  """
  A source that is actually a a feed (typically RSS or Atom).
  """
  # The URL where to get updated list of References from
  xmlURL = models.CharField(max_length=URL_MAX_LENGTH)
  # Date marking the last time the source was checked for an update
  # TODO:rename in last[_update]_check, last_probing or something like that
  last_update = models.DateTimeField('last update')


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
