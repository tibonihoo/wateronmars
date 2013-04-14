from django.db import models

from wom_classification.models import Tag


# Max number of characters in a URL.
# Let's make it long enough to get twice the (not so) good old Windows
# path limit.
# WARNING: READ ONLY !
URL_MAX_LENGTH = 512

# Max number of characters for a source name.
# Let's make it long enough to get a 140 char tweet plus a little extra.
# WARNING: READ ONLY !
SOURCE_NAME_MAX_LENGTH = 150

# Max number of characters for a reference title.
# Let's make it long enough to get a 140 char tweet plus a little extra.
# WARNING: READ ONLY !
REFERENCE_TITLE_MAX_LENGTH = 150


class Source(models.Model):
  """
  Describe the origin of one or many references.
  """
  # The URL identifies a source (and URLs will be used as URIs), must be unique and used as a db_index
  url = models.CharField(max_length=URL_MAX_LENGTH, unique=True)
  # A human friendly "identification" of the source
  name = models.CharField(max_length=SOURCE_NAME_MAX_LENGTH)
  # A short and optional descriptive text 
  description = models.TextField(default="")
  # Indicate wether this source may be shared and displayed publicly
  is_public = models.BooleanField(default=False)
  # Tags used (at least) for user-explicit classification
  tags  = models.ManyToManyField(Tag)
  
  def __unicode__(self):
    return "%s (%s)" % (self.name,self.url)


class Reference(models.Model): # A pebble !
  """
  The most basic item representing a piece of information on the
  internet (aka a bookmark or a newsitem).
  """
  # The URL identifies a source (and URLs will be used as URIs), must be unique and used as a db_index
  url   = models.CharField(max_length=URL_MAX_LENGTH)
  # Title of the reference (compulsory)
  title = models.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH)
  # A short summary about the reference's content
  description = models.TextField(default="")
  # Tells when the reference was first published, as a timezone-aware
  # datetime object.
  pub_date = models.DateTimeField('date published')
  # Indicate wether this source may be shared and displayed publicly
  is_public = models.BooleanField(default=False)
  # The source from which this reference item comes from
  source = models.ForeignKey(Source)
  # Tags used (at least) for user-explicit classification  
  tags  = models.ManyToManyField(Tag)
  # Count the number of users that saved this reference
  save_count = models.IntegerField(default=0)
  
  def __unicode__(self):
    return "%s (%s)" % (self.title,self.url)



