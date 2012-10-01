from django.db import models

from wom_pebbles.models import Source
from wom_pebbles.models import URL_MAX_LENGTH

class FeedSource(Source):
  """
  A source that is actually a a feed (typically RSS or Atom).
  """
  # The URL where to get updated list of References from
  xmlURL = models.CharField(max_length=URL_MAX_LENGTH)
  # Date marking the last time the source was checked for an update
  last_update = models.DateTimeField('last update')

