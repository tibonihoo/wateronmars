from django.db import models

# Limit for tag names, read-only and provided for convenience in
# sanity checks.
# NOTE: from http://www.fun-with-words.com/word_longest.html
# I get that the longest word in the world (chemicals aparts) seems
# to be a 85 character one, not sure all languages are covered but
# let's make the limit 100 to be on the safe side.
# WARNING: READ ONLY !
TAG_NAME_MAX_LENGTH = 100


class Tag(models.Model):
  """
  Just a label as the most basic and at the same a quite powerful classification tool.
  """
  # A simple string to be used for classification
  name = models.CharField(max_length=TAG_NAME_MAX_LENGTH, unique=True, db_index=True)
  # Indicate wether this tag may be shared and displayed publicly
  is_public = models.BooleanField(default=False)
  
  def __unicode__(self):
    return self.name
  
