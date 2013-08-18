# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 4 -*-

import datetime
from django.utils import timezone

from django.test import TestCase

from wom_pebbles.models import Reference

from wom_river.models import FeedSource
from wom_river.models import URL_MAX_LENGTH
from wom_river.models import ReferenceUserStatus

from django.contrib.auth.models import User

class FeedSourceModelTest(TestCase):

    def setUp(self):
        self.test_date = datetime.datetime.now(timezone.utc)

    def test_construction_defaults(self):
        """
        This tests just makes it possible to double check that a
        change in the default is voluntary.
        """
        s = FeedSource.objects.create(xmlURL="http://mouf/bla.xml",
                                      last_update=self.test_date,
                                      url="http://mouf",name="glop")
        self.assertEqual(s.xmlURL,"http://mouf/bla.xml")
        self.assertEqual(s.last_update,self.test_date)
        # only Source's default public flag
        self.assertEqual(s.is_public,False)
        
    def test_construction_with_max_length_xmlURL(self):
        """
        Test that the max length constant guarantees that a string of
        the corresponding length will be accepted.
        """
        max_length_xmlURL = "x"*URL_MAX_LENGTH
        s = FeedSource.objects.create(xmlURL=max_length_xmlURL,
                                      last_update=self.test_date,
                                      url="http://mouf",name="glop")
        # Check also that url wasn't truncated
        self.assertEqual(max_length_xmlURL,s.xmlURL)


class ReferenceUserStatusModelTest(TestCase):

    def setUp(self):
        self.test_date = datetime.datetime.now(timezone.utc)
        test_source = FeedSource.objects.create(xmlURL="http://bla/hop.xml",last_update=self.test_date,url="http://mouf",name="glop")
        self.test_reference = Reference.objects.create(url="http://mouf",title="glop",
                                                       pub_date=self.test_date,source=test_source)
        self.test_user = User.objects.create(username="name")
        
    def test_construction_defaults(self):
        """
        This tests just makes it possible to double check that a
        change in the default is voluntary.
        """
        rust = ReferenceUserStatus.objects.create(ref=self.test_reference,
                                                  user=self.test_user,
                                                  ref_pub_date=self.test_date)
        self.assertFalse(rust.has_been_read)
        self.assertFalse(rust.has_been_saved)
