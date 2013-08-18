# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 4 -*-

import datetime
from django.utils import timezone

from django.test import TestCase
from django.db import IntegrityError

from wom_pebbles.models import Source
from wom_pebbles.models import Reference
from wom_pebbles.models import URL_MAX_LENGTH
from wom_pebbles.models import SOURCE_NAME_MAX_LENGTH
from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH


class SourceModelTest(TestCase):
    
    def test_construction_defaults(self):
        """
        This tests just makes it possible to double check that a
        change in the default is voluntary.
        """
        s = Source.objects.create(url="http://mouf",name="glop")
        self.assertEqual(s.url,"http://mouf")
        self.assertEqual(s.name,"glop")
        self.assertFalse(s.is_public)
        self.assertEqual(s.description,"")
        
    def test_construction_with_max_length_url(self):
        """
        Test that the max length constant guarantees that a string of
        the corresponding length will be accepted.
        """
        max_length_url = "u"*URL_MAX_LENGTH
        s = Source.objects.create(url=max_length_url,name="glop")
        # Check also that url wasn't truncated
        self.assertEqual(max_length_url,s.url)

    def test_construction_with_max_length_name(self):
        """
        Test that the max length constant guarantees that a string of
        the corresponding length will be accepted.
        """
        max_length_name = "u"*SOURCE_NAME_MAX_LENGTH
        s = Source.objects.create(url="http://mouf",name=max_length_name)
        # Check also that name wasn't truncated
        self.assertEqual(max_length_name,s.name)
        
    def test_unicity_of_urls(self):
        """
        Test the unicity guaranty on names.
        """
        s = Source.objects.create(url="http://mouf",name="glop")
        self.assertRaises(IntegrityError,Source.objects.create,url=s.url,name="paglop")


class ReferenceModelTest(TestCase):

    def setUp(self):
        self.test_source = Source.objects.create(url="http://mouf",name="glop")
        self.test_date = datetime.datetime.now(timezone.utc)
        
    def test_construction_defaults(self):
        """
        This tests just makes it possible to double check that a
        change in the default is voluntary.
        """
        r = Reference.objects.create(url="http://mouf",title="glop",
                                     pub_date=self.test_date,source=self.test_source)
        
        self.assertEqual(r.url,"http://mouf")
        self.assertEqual(r.title,"glop")
        self.assertFalse(r.is_public)
        self.assertEqual(r.description,"")
        
    def test_construction_with_max_length_url(self):
        """
        Test that the max length constant guarantees that a string of
        the corresponding length will be accepted.
        """
        max_length_url = "u"*URL_MAX_LENGTH
        r = Reference.objects.create(url=max_length_url,title="glop",pub_date=self.test_date,source=self.test_source)
        # Check also that url wasn't truncated
        self.assertEqual(max_length_url,r.url)

    def test_construction_with_max_length_title(self):
        """
        Test that the max length constant guarantees that a string of
        the corresponding length will be accepted.
        """
        max_length_title = "u"*REFERENCE_TITLE_MAX_LENGTH
        s = Reference.objects.create(url="http://mouf",title=max_length_title,pub_date=self.test_date,source=self.test_source)
        # Check also that title wasn't truncated
        self.assertEqual(max_length_title,s.title)
        
