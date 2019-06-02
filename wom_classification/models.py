# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2013 Thibauld Nion
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
from django.db import transaction

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


from django.contrib.auth.models import User


# Limit for tag names, read-only and provided for convenience in
# sanity checks.
# NOTE: from http://www.fun-with-words.com/word_longest.html
# I get that the longest word in the world (chemicals aparts) seems
# to be a 85 character one, not sure all languages are covered but
# let's make the limit 100 to be on the safe side.
# WARNING: READ ONLY !
TAG_NAME_MAX_LENGTH = 100

class Tag(models.Model):
  """Just a label as the most basic and at the same a quite powerful
  classification tool."""
  
  # A simple string to be used for classification
  name = models.CharField(max_length=TAG_NAME_MAX_LENGTH,
                          unique=True, db_index=True)
  
  def __str__(self):
    return self.name

    
class ClassificationData(models.Model):  
  """Represent the association of a model instance (whatever the model)
  and its user-specific classification data ("features" in machine
  learning terminology)."""
  
  owner = models.ForeignKey(User, on_delete=models.CASCADE)
  
  tags = models.ManyToManyField(Tag)
  
  content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
  object_id = models.PositiveIntegerField()
  content_object = GenericForeignKey('content_type', 'object_id')
  
  def __str__(self):
    return "%s>%s: %s" % (self.owner.username,
                           self.content_object,
                           list(t for t in self.tags.all()))

  
def get_item_tags(user,item):
  """Return a QuerySet referencing all Tags attributed by the user to the item."""
  item_type = ContentType.objects.get_for_model(item)
  qs = ClassificationData.objects.filter(owner=user,
                                         content_type=item_type,
                                         object_id=item.id)
  numRes = qs.count()
  if numRes==0:
    return Tag.objects.none()
  else:
    if numRes>1:
      print("WARNING: unexpectedly found more than one CD for %s's%s" % (user,item))
    # in any case return the first tags
    return qs[0].tags


def get_item_tag_names(user,item):
  """Return the list of the names of Tags attributed by the user to the item."""
  return [t.name for t in get_item_tags(user,item).all()]


def get_all_users_tags_for_item(item):
  """Return a QuerySet for Tags attributed by any user to the item.""" 
  item_type = ContentType.objects.get_for_model(item)
  return Tag.objects.filter(classificationdata__content_type=item_type,
                            classificationdata__object_id=item.id)
  
def set_item_tags(user,item,tags):
  """Add specified tags to a given item on behalf of a specific user.
  
  If the item has no ClassificationData associated to this user, it
  will be created and saved in the database.
  """
  item_type = ContentType.objects.get_for_model(item)
  qs = ClassificationData.objects.filter(owner=user,
                                         content_type=item_type,
                                         object_id=item.id)
  numRes = qs.count()
  if numRes==0:
    cd = ClassificationData(owner=user,content_object=item)
    cd.save()
  else:
    if numRes>1:
      print("WARNING: unexpectedly found more than one CD for %s's%s" % (user,item))
    cd = qs[0]
  cd.tags.add(*tags)
  return cd
  
def set_item_tag_names(user,item,names):
  """Add specified tags corresponding to the given names to the item on
  behalf of a specific user.
  
  If a name doesn't match an existing Tag instance a new one is created and saved.
  """
  tag_list = []
  new_tags = []
  for tag_name in names:
    if Tag.objects.filter(name=tag_name).exists():
      tag_list.append(Tag.objects.get(name=tag_name))
    else:
      t = Tag(name=tag_name)
      new_tags.append(t)
  with transaction.atomic():
    for t in new_tags:
      t.save()
  return set_item_tags(user,item,tag_list+new_tags)
  
def get_user_tags(user):
  """Return a QuerySet referencing all tags set by a given user."""
  return Tag.objects.filter(classificationdata__owner=user).distinct()

def select_model_items_with_tags(user,model,tags):
  """Return a QuerySet referencing all items of the specified models
  that has been attributed a given set of tags by the user."""
  model_type = ContentType.objects.get_for_model(model)
  qs = ClassificationData.objects.filter(owner=user,
                                         content_type=model_type)
  for tag in tags:
    qs = qs.filter(tags=tag)
  item_id_set = set([cd.object_id for cd in qs])
  return model.objects.filter(id__in=item_id_set)

  
