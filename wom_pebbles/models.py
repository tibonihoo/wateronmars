# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

from django.db import models


# Max number of characters in a URL.
# Let's make it long enough to get twice the (not so) good old Windows
# path limit.
# WARNING: READ ONLY !
URL_MAX_LENGTH = 255

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
  # The URL identifies a source (and URLs will be used as URIs), must
  # be unique and used as a db_index
  url = models.CharField(max_length=URL_MAX_LENGTH, unique=True)
  # A human friendly "identification" of the source
  name = models.CharField(max_length=SOURCE_NAME_MAX_LENGTH)
  # A short and optional descriptive text 
  description = models.TextField(default="")
  
  def __unicode__(self):
    return "%s[%s]" % (self.name,self.url)


class Reference(models.Model): # A pebble !
  """
  The most basic item representing a piece of information on the
  internet (aka a bookmark or a newsitem).
  """
  # The URL identifies a reference (and URLs will be used as URIs),
  # but several references may share the same URL especially if they
  # have been published by different sources.
  url = models.CharField(max_length=URL_MAX_LENGTH)
  # Title of the reference (compulsory)
  title = models.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH)
  # A short summary about the reference's content.
  # WARNING: this is for a description provided by the author of the
  # reference, visible to everybody. User-specific description should
  # better be stored in another "model".
  description = models.TextField(default="")
  # Tells when the reference was first published, as a timezone-aware
  # datetime object.
  pub_date = models.DateTimeField('date published')
  # The source from which this reference item comes from
  source = models.ForeignKey(Source)
  # Count the number of users that saved this reference
  save_count = models.IntegerField(default=0)
  
  def __unicode__(self):
    return "%s[%s]" % (self.title,self.url)
