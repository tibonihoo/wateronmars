# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

import datetime
from django.utils import timezone

from django.test import TestCase

from wom_pebbles.models import Reference
from wom_pebbles.models import Source

from wom_river.models import FeedSource
from wom_river.models import URL_MAX_LENGTH
from wom_river.models import ReferenceUserStatus

from wom_river.tasks import import_feedsources_from_opml

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
                                  last_update_check=self.test_date,
                                  url="http://mouf",name="glop")
    self.assertEqual(s.xmlURL,"http://mouf/bla.xml")
    self.assertEqual(s.last_update_check,self.test_date)
    
  def test_construction_with_max_length_xmlURL(self):
    """
    Test that the max length constant guarantees that a string of
    the corresponding length will be accepted.
    """
    max_length_xmlURL = "x"*URL_MAX_LENGTH
    s = FeedSource.objects.create(xmlURL=max_length_xmlURL,
                                  last_update_check=self.test_date,
                                  url="http://mouf",name="glop")
    # Check also that url wasn't truncated
    self.assertEqual(max_length_xmlURL,s.xmlURL)


class ReferenceUserStatusModelTest(TestCase):

  def setUp(self):
    self.test_date = datetime.datetime.now(timezone.utc)
    test_source = FeedSource.objects.create(xmlURL="http://bla/hop.xml",last_update_check=self.test_date,url="http://mouf",name="glop")
    self.test_reference = Reference.objects.create(url="http://mouf",
                                                   title="glop",
                                                   pub_date=self.test_date,
                                                   source=test_source)
    self.user = User.objects.create(username="name")
    
  def test_construction_defaults(self):
    """
    This tests just makes it possible to double check that a
    change in the default is voluntary.
    """
    rust = ReferenceUserStatus.objects.create(ref=self.test_reference,
                                              user=self.user,
                                              ref_pub_date=self.test_date)
    self.assertFalse(rust.has_been_read)
    self.assertFalse(rust.has_been_saved)



    
class ImportFeedSourcesFromOPMLTaskTest(TestCase):
  
  def setUp(self):
    # Create 2 users but only create sources for one of them.
    self.user1 = User.objects.create_user(username="uA",password="pA")
    # self.user1_profile = UserProfile.objects.create(user=self.user1)
    # self.user2 = User.objects.create_user(username="uB",password="pB")
    # self.user2_profile = UserProfile.objects.create(user=self.user2)
    test_date = datetime.datetime.now(timezone.utc)
    self.fs1 = FeedSource.objects.create(xmlURL="http://mouf/rss.xml",
                                         last_update_check=test_date,
                                         url="http://mouf",name="f1")
    self.fs3 = FeedSource.objects.create(xmlURL="http://greuh/rss.xml",
                                         last_update_check=test_date,
                                         url="http://greuh",name="f3")
    # self.user1_profile.feed_sources.add(fs1)
    # self.user1_profile.feed_sources.add(fs3)
    # self.user1_profile.sources.add(fs1)
    # self.user1_profile.sources.add(fs3)
    # also add plain sources
    self.s1 = Source.objects.create(url="http://s1",name="s1")
    self.s3 = Source.objects.create(url="http://s3",name="s3")
    # self.user1_profile.sources.add(s1)
    # self.user1_profile.sources.add(s3)
    # create an opml snippet
    opml_txt = """\
<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
  <title>My Subcriptions</title>
  </head>
  <body>
  <outline title="News" text="News">
    <outline text="Richard Stallman's Political Notes"
         title="Richard Stallman's Political Notes" type="rss"
         xmlUrl="http://stallman.org/rss/rss.xml" htmlUrl="http://stallman.org/archives/polnotes.html"/>
    <outline text="Mouf"
         title="Mouf" type="rss"
         xmlUrl="http://mouf/rss.xml" htmlUrl="http://mouf"/>
    <outline text="Dave's LifeLiner" title="Dave's LifeLiner"
         type="rss" xmlUrl="http://www.scripting.com/rss.xml" htmlUrl="http://scripting.com/"/>
  </outline>
  <outline title="Culture" text="Culture">
    <outline text="Open Culture" title="Open Culture" type="rss"
         xmlUrl="http://www.openculture.com/feed" htmlUrl="http://www.openculture.com"/>
  </outline>
  </body>
</opml>
"""
    self.feeds_and_tags = import_feedsources_from_opml(opml_txt)
    
  def test_check_sources_correctly_added(self):
    self.assertEqual(7,Source.objects.count())
    self.assertEqual(5,FeedSource.objects.count())
    self.assertIn("http://stallman.org/rss/rss.xml",
                  [s.xmlURL for s in FeedSource.objects.all()])
    self.assertIn("http://www.scripting.com/rss.xml",
                  [s.xmlURL for s in FeedSource.objects.all()])
    self.assertIn("http://www.openculture.com/feed",
                  [s.xmlURL for s in FeedSource.objects.all()])
  
  def test_check_sources_correctly_returned(self):
    self.assertEqual(4,len(self.feeds_and_tags.keys()))
    returned_xmlURLs = [s.xmlURL for s in self.feeds_and_tags.keys()]
    self.assertIn("http://stallman.org/rss/rss.xml",returned_xmlURLs)
    self.assertIn("http://www.scripting.com/rss.xml",returned_xmlURLs)
    self.assertIn("http://www.openculture.com/feed",returned_xmlURLs)
        
    
  def test_check_tags_correctly_associated_to_sources(self):
    # Check that tags were correctly associated with the sources
    f = FeedSource.objects.get(url="http://scripting.com/")
    self.assertIn("News",self.feeds_and_tags[f])
    f = FeedSource.objects.get(url="http://stallman.org/archives/polnotes.html")
    self.assertIn("News",self.feeds_and_tags[f])
    f = FeedSource.objects.get(url="http://mouf")
    self.assertIn("News",self.feeds_and_tags[f])
    f = FeedSource.objects.get(url="http://www.openculture.com")
    self.assertIn("Culture",self.feeds_and_tags[f])


