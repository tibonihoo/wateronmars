# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 4 -*-

from django.test import TestCase
from django.db import IntegrityError

from wom_classification.models import Tag
from wom_classification.models import TAG_NAME_MAX_LENGTH

class TagModelTest(TestCase):
    
    def test_construction_defaults(self):
        """
        Test the defaults values guaranteed at construction time.
        """
        t = Tag.objects.create(name="mouf")
        self.assertEqual("mouf",t.name)
        self.assertFalse(t.is_public)
        
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
        
                          
        
