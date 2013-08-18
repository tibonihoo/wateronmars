# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 4 -*-

import datetime
from django.utils import timezone

from django.test import TestCase

from wom_pebbles.models import Reference
from wom_pebbles.models import Source

from wom_user.models import UserProfile
from wom_user.models import UserBookmark

from django.contrib.auth.models import User


class UserProfileModelTest(TestCase):

    def setUp(self):
        self.test_user = User.objects.create(username="name")
        
    def test_accessible_info(self):
        """
        Just to be sure what info we can access (not a "unit" test per
        se but useful anyway to make sure the model given enough
        information and list the info we rely on)
        """
        p = UserProfile.objects.create(user=self.test_user)
        self.assertEqual(p.user,self.test_user)
        self.assertEqual(0,len(p.tags.all()))
        self.assertEqual(0,len(p.sources.all()))
        self.assertEqual(0,len(p.feed_sources.all()))
        # just to be sure
        self.assertNotEqual(p.user.date_joined,None)


class UserBookmarkModelTest(TestCase):

    def setUp(self):
        self.test_date = datetime.datetime.now(timezone.utc)
        test_source = Source.objects.create(url="http://mouf",name="glop")
        self.test_reference = Reference.objects.create(url="http://mouf",
                                                       title="glop",
                                                       pub_date=self.test_date,
                                                       source=test_source)
        self.test_user = User.objects.create(username="name")
        
    def test_construction_defaults(self):
        """
        This tests just makes it possible to double check that a
        change in the default is voluntary.
        """
        b = UserBookmark.objects.create(owner=self.test_user,
                                        reference=self.test_reference,
                                        saved_date=self.test_date)
        self.assertFalse(b.is_public)
        self.assertEqual(0,len(b.tags.all()))
