# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 4 -*-

from django.test import TestCase
from django.db import IntegrityError

from django.contrib.auth.models import User

from wom_classification.models import Tag
from wom_classification.models import TAG_NAME_MAX_LENGTH
from wom_classification.models import ClassificationData
from wom_classification.models import get_item_tags
from wom_classification.models import get_item_tag_names
from wom_classification.models import get_all_users_tags_for_item 
from wom_classification.models import set_item_tags
from wom_classification.models import set_item_tag_names
from wom_classification.models import get_user_tags
from wom_classification.models import select_model_items_with_tags


if TAG_NAME_MAX_LENGTH>255:
    print "WARNING: the current max length for TAG name may cause portability problems (see https://docs.djangoproject.com/en/1.4/ref/databases/#character-fields)"


class TagModelTest(TestCase):
    
    def test_construction_defaults(self):
        """
        Test the defaults values guaranteed at construction time.
        """
        t = Tag.objects.create(name="mouf")
        self.assertEqual("mouf",t.name)
        
    def test_construction_with_max_name(self):
        """
        Test that the max length constant guarantees that a string of
        the corresponding length will be accepted.
        """
        max_length_name = "m"*TAG_NAME_MAX_LENGTH
        t = Tag.objects.create(name=max_length_name)
        # Check also that the name wasn't truncated
        self.assertEqual(max_length_name,t.name)
        
    def test_unicity_of_names(self):
        """
        Test the unicity guaranty on names.
        """
        t = Tag.objects.create(name="mouf")
        self.assertRaises(IntegrityError,Tag.objects.create,name=t.name)
        
class ClassificationDataModelTest(TestCase):
        
    def setUp(self):
        self.user_a = User.objects.create(username="UserA")
        self.user_b = User.objects.create(username="UserB")
        
    def test_construction_for_any_model_instance(self):
        item = User.objects.create(username="C")
        ClassificationData.objects.create(owner=self.user_a,
                                          content_object=item)
        nbItemCD = ClassificationData.objects.filter(object_id=item.id).count()
        self.assertEqual(1,nbItemCD)
        nbUserACD = ClassificationData.objects.filter(owner=self.user_a).count()
        self.assertEqual(1,nbUserACD)
        nbUserBCD = ClassificationData.objects.filter(owner=self.user_b).count()
        self.assertEqual(0,nbUserBCD)

    def test_stringification(self):
        """Test the __unicode__ method since it is slightly non-trivial."""
        item = User.objects.create(username="ItemC")
        ci = ClassificationData.objects.create(owner=self.user_a,
                                          content_object=item)
        unicodeStr = unicode(ci)
        self.assertIn("ItemC",unicodeStr)
        self.assertIn("UserA",unicodeStr)

class ClassificationDataManipulationTest(TestCase):
    """Test functions dedicated to easily browse the relations between the
    generic ClassificationData and a specific model instance."""

    def setUp(self):
        self.user_a = User.objects.create(username="UserA")
        self.user_b = User.objects.create(username="UserB")
        self.tag_mouf = Tag.objects.create(name="mouf")
        self.tag_glop = Tag.objects.create(name="glop")
        self.tag_blah = Tag.objects.create(name="blah")
        self.tag_hop  = Tag.objects.create(name="hop")
        self.item_1 = User.objects.create(username="Item1")
        self.item_2 = Tag.objects.create(name="Item2")
        self.user_a_cd_1 = ClassificationData\
            .objects.create(owner=self.user_a,content_object=self.item_1)
        self.user_a_cd_1.tags.add(self.tag_mouf,self.tag_glop)
        self.user_a_cd_2 = ClassificationData\
            .objects.create(owner=self.user_a,content_object=self.item_2)
        self.user_a_cd_2.tags.add(self.tag_mouf,self.tag_hop)
        self.user_b_cd_1 = ClassificationData\
            .objects.create(owner=self.user_b,content_object=self.item_1)
        self.user_b_cd_1.tags.add(self.tag_blah)
        self.item_unc = Tag.objects.create(name="unclassified")
        
    def test_get_item_tags(self):
        tagQuerySet = get_item_tags(self.user_a,self.item_1)
        self.assertEqual(2,tagQuerySet.count())
        self.assertIn(self.tag_mouf,tagQuerySet.all())
        self.assertIn(self.tag_glop,tagQuerySet.all())

    def test_get_item_tags_for_unclassified_item(self):
        tagQuerySet = get_item_tags(self.user_a,self.item_unc)
        self.assertEqual(0,tagQuerySet.count())

    def test_get_item_tag_names(self):
        nameList = get_item_tag_names(self.user_a,self.item_1)
        self.assertEqual(2,len(nameList))
        self.assertIn("mouf",nameList)
        self.assertIn("glop",nameList)
        
    def test_set_item_tags(self):
        new_tag = Tag.objects.create(name="new")
        cd = set_item_tags(self.user_a,self.item_1,[self.tag_blah,new_tag])
        self.assertEqual(4,cd.tags.count())
        self.assertIn(self.tag_blah,cd.tags.all())
        self.assertIn(new_tag,cd.tags.all())
        
    def test_set_item_tags_for_unclassified_item(self):
        new_tag = Tag.objects.create(name="new")
        cd = set_item_tags(self.user_a,self.item_unc,[self.tag_blah,new_tag])
        self.assertEqual(2,cd.tags.count())
        self.assertIn(self.tag_blah,cd.tags.all())
        self.assertIn(new_tag,cd.tags.all())
    
    def test_set_item_tag_names(self):
        cd = set_item_tag_names(self.user_a,self.item_1,["blah","new"])
        self.assertEqual(4,cd.tags.count())
        tag_names = [t.name for t in cd.tags.all()]
        self.assertIn("blah", tag_names)
        self.assertIn("new", tag_names)        
    
    def test_get_item_tags_for_all_users(self):
        tagSet = get_all_users_tags_for_item(self.item_1)
        self.assertEqual(3,len(tagSet))
        self.assertIn(self.tag_mouf,tagSet)
        self.assertIn(self.tag_glop,tagSet)
        self.assertIn(self.tag_blah,tagSet)
    
    def test_get_item_tags_for_all_users_for_unclassified_item(self):
        tagSet = get_all_users_tags_for_item(self.item_unc)
        self.assertEqual(0,len(tagSet))
        
    def test_get_user_tags(self):
        tagSet = get_user_tags(self.user_a)
        self.assertEqual(3,len(tagSet))
        self.assertIn(self.tag_mouf,tagSet)
        self.assertIn(self.tag_glop,tagSet)
        self.assertIn(self.tag_hop,tagSet)
        
    def test_select_model_items_with_tags(self):
        itemQuerySet = select_model_items_with_tags(self.user_a,Tag,
                                                    [self.tag_mouf])
        self.assertEqual(1,itemQuerySet.count())
        self.assertIn(self.item_2,itemQuerySet.all())
        
    def test_select_model_items_with_tags_no_result(self):
        itemQuerySet = select_model_items_with_tags(self.user_a,Tag,
                                                    [self.tag_mouf,self.tag_blah])
        self.assertEqual(0,itemQuerySet.count())
        
