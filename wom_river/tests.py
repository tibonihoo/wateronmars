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

from datetime import datetime
from django.utils import timezone

import feedparser

from django.test import TestCase

from wom_pebbles.models import Reference

from wom_river.models import WebFeed
from wom_river.models import URL_MAX_LENGTH

from wom_river.tasks import import_feedsources_from_opml
from wom_river.tasks import add_new_references_from_feedparser_entries

from django.contrib.auth.models import User

class WebFeedModelTest(TestCase):

  def setUp(self):
    self.date = datetime.now(timezone.utc)

  def test_construction_defaults(self):
    """
    This tests just makes it possible to double check that a
    change in the default is voluntary.
    """
    r = Reference.objects.create(url="http://mouf",
                                 pub_date=self.date)
    s = WebFeed.objects.create(xmlURL="http://mouf/bla.xml",
                               last_update_check=self.date,
                               source=r)
    self.assertEqual(s.xmlURL,"http://mouf/bla.xml")
    self.assertEqual(s.last_update_check,self.date)
    
  def test_construction_with_max_length_xmlURL(self):
    """
    Test that the max length constant guarantees that a string of
    the corresponding length will be accepted.
    """
    r = Reference.objects.create(url="http://mouf",
                                 pub_date=self.date)
    max_length_xmlURL = "x"*URL_MAX_LENGTH
    s = WebFeed.objects.create(xmlURL=max_length_xmlURL,
                               last_update_check=self.date,
                               source=r)
    # Check also that url wasn't truncated
    self.assertEqual(max_length_xmlURL,s.xmlURL)

    
class ImportFeedSourcesFromOPMLTaskTest(TestCase):
  
  def setUp(self):
    # Create 2 users but only create sources for one of them.
    self.user1 = User.objects.create_user(username="uA",password="pA")
    # self.user1_profile = UserProfile.objects.create(user=self.user1)
    # self.user2 = User.objects.create_user(username="uB",password="pB")
    # self.user2_profile = UserProfile.objects.create(user=self.user2)
    date = datetime.now(timezone.utc)
    r1 = Reference.objects.create(url="http://mouf",title="f1",pub_date=date)
    self.fs1 = WebFeed.objects.create(xmlURL="http://mouf/rss.xml",
                                      last_update_check=date,
                                      source=r1)
    r3 = Reference.objects.create(url="http://greuh",title="f3",pub_date=date)
    self.fs3 = WebFeed.objects.create(xmlURL="http://greuh/rss.xml",
                                      last_update_check=date,
                                      source=r3)
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
    <outline text="Dave&#39;s LifeLiner" title="Dave&#39;s LifeLiner"
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
    self.assertEqual(5,WebFeed.objects.count())
    self.assertIn("http://stallman.org/rss/rss.xml",
                  [s.xmlURL for s in WebFeed.objects.all()])
    self.assertEqual("Richard Stallman's Political Notes",
                     WebFeed.objects.get(
                       xmlURL="http://stallman.org/rss/rss.xml").source.title)
    self.assertIn("http://www.scripting.com/rss.xml",
                  [s.xmlURL for s in WebFeed.objects.all()])
    self.assertEqual("Dave's LifeLiner",
                     WebFeed.objects.get(
                       xmlURL="http://www.scripting.com/rss.xml").source.title)
    self.assertIn("http://www.openculture.com/feed",
                  [s.xmlURL for s in WebFeed.objects.all()])
    self.assertEqual("Open Culture",
                     WebFeed.objects.get(
                       xmlURL="http://www.openculture.com/feed").source.title)
    
  def test_check_sources_correctly_returned(self):
    self.assertEqual(4,len(list(self.feeds_and_tags.keys())))
    returned_xmlURLs = [s.xmlURL for s in self.feeds_and_tags.keys()]
    self.assertIn("http://stallman.org/rss/rss.xml",returned_xmlURLs)
    self.assertIn("http://www.scripting.com/rss.xml",returned_xmlURLs)
    self.assertIn("http://www.openculture.com/feed",returned_xmlURLs)
        
    
  def test_check_tags_correctly_associated_to_sources(self):
    # Check that tags were correctly associated with the sources
    f = WebFeed.objects.get(xmlURL="http://www.scripting.com/rss.xml")
    self.assertIn("News",self.feeds_and_tags[f])
    f = WebFeed.objects.get(xmlURL="http://stallman.org/rss/rss.xml")
    self.assertIn("News",self.feeds_and_tags[f])
    f = WebFeed.objects.get(xmlURL="http://mouf/rss.xml")
    self.assertIn("News",self.feeds_and_tags[f])
    f = WebFeed.objects.get(xmlURL="http://www.openculture.com/feed")
    self.assertIn("Culture",self.feeds_and_tags[f])



class AddReferencesFromFeedParserEntriesTask(TestCase):

  def setUp(self):
    date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
      url="http://example.com",
      title="Test Source",
      pub_date=date)
    web_feed  = WebFeed.objects.create(xmlURL="http://mouf/rss.xml",
                                       source=self.source,
                                       last_update_check=\
                                       datetime.utcfromtimestamp(0)\
                                       .replace(tzinfo=timezone.utc))
    # RSS from a source that already has a mapping
    rss_xml = """\
<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Source</title>
    <link>http://example.com/test_source</link>
    <description>A RSS test source</description>
    <pubDate>Sun, 17 Nov 2013 19:08:15 GMT</pubDate>
    <lastBuildDate>Sun, 17 Nov 2013 19:08:15 GMT</lastBuildDate>
    <language>en-us</language>
    <generator>Testor</generator>
    <docs>http://cyber.law.harvard.edu/rss/rss.html</docs>
    <item>
      <link>http://www.example.com</link>
      <description>&lt;p>An example bookmark.&lt;/p>
      </description>
      <pubDate>Sun, 17 Nov 2013 19:01:58 GMT</pubDate>
      <guid>http://www.example.com</guid>
      <category>example</category>
      <category>html</category>
    </item>
    <item>
      <title>Long</title>
      <link>http://%s</link>
      <description>&lt;p>Too long&lt;/p>
      </description>
      <category>test</category>
      <pubDate>Sun, 17 Nov 2013 16:56:06 GMT</pubDate>
      <guid>http://%s</guid>
    </item>
    <item>
      <title>The mouf</title>
      <link>http://mouf/a</link>
      <category>test</category>
      <description>&lt;p>This is just a test&lt;/p>
      </description>
      <pubDate>Sun, 17 Nov 2013 16:56:06 GMT</pubDate>
      <guid>http://mouf/a</guid>
    </item>
  </channel>
</rss>
""" % ("u"*(URL_MAX_LENGTH),"u"*(URL_MAX_LENGTH))
    
    f1 = feedparser.parse(rss_xml)
    self.ref_and_tags = add_new_references_from_feedparser_entries(web_feed,
                                                                   f1.entries)
    
  def test_references_are_added_with_correct_urls(self):
    references_in_db = list(Reference.objects.all())
    self.assertEqual(4,len(references_in_db))
    ref_urls = [r.url for r in references_in_db]
    self.assertIn("http://www.example.com",ref_urls)
    self.assertIn("http://mouf/a",ref_urls)
    max_length_urls = [u for u in ref_urls if len(u)==URL_MAX_LENGTH]
    self.assertEqual(1,len(max_length_urls))
    self.assertTrue(max_length_urls[0].startswith("http://uuu"))
    
  def test_references_are_added_with_correct_title(self):
    ref_title = Reference.objects.get(url="http://www.example.com").title
    self.assertEqual("An example bookmark.",ref_title)
    ref_title = Reference.objects.get(url="http://mouf/a").title
    self.assertEqual("The mouf",ref_title)
    ref_title = Reference.objects.get(url__contains="uuu").title 
    self.assertEqual("Long",ref_title)
    # Additional check here to see if we managed to use the
    # description field to 'save' url info from oblivion.
    self.assertIn("http://uuu",
                  Reference.objects.get(url__contains="uuu").description)
    
  def test_references_are_added_with_correct_sources(self):
    references_in_db = list(Reference.objects.all())
    self.assertEqual(4,len(references_in_db))
    for ref in references_in_db:
      if ref!=self.source:
        self.assertIn(self.source,ref.sources.all(),ref)
    
  def test_check_metadata_correctly_associated_to_refs(self):
    self.assertEqual(3,len(self.ref_and_tags))
    urls = [r.url for r in self.ref_and_tags]
    urls.sort(key=lambda u:len(u))
    self.assertIn("http://www.example.com",urls)
    self.assertIn("http://mouf/a",urls)
    self.assertTrue(urls[-1].startswith("http://uuu"))
    tags = self.ref_and_tags[
      Reference.objects.get(url="http://www.example.com")]
    self.assertEqual(set(["example","html"]),set(tags))
    tags = self.ref_and_tags[
      Reference.objects.get(url="http://mouf/a")]
    self.assertEqual(set(["test"]),set(tags))
    tags = self.ref_and_tags[
      Reference.objects.get(url=urls[-1])]
    self.assertEqual(set(["test"]),set(tags))

class AddReferencesFromFeedParserTaskOnBrokenFeed(TestCase):

  def setUp(self):
    date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
      url="http://example.com",
      title="Test Source",
      pub_date=date)
    web_feed  = WebFeed.objects.create(xmlURL="http://mouf/rss.xml",
                                       source=self.source,
                                       last_update_check=\
                                       datetime.utcfromtimestamp(0)\
                                       .replace(tzinfo=timezone.utc))
    # RSS from a source that already has a mapping
    rss_xml = """\
<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Source</title>
    <link>http://example.com/test_source</link>
    <description>A RSS test source</description>
    <pubDate>Sun, 17 Nov 2013 19:08:15 GMT</pubDate>
    <lastBuildDate>Sun, 17 Nov 2013 19:08:15 GMT</lastBuildDate>
    <language>en-us</language>
    <generator>Testor</generator>
    <docs>http://cyber.law.harvard.edu/rss/rss.html</docs>
    <item>
      <link>http://www.example.com</link>
      <description>&lt;p>An example bookmark.&lt;/p>
      </description>
      <!-- No pubDate -->
      <guid>http://www.example.com</guid>
      <category>example</category>
      <category>html</category>
    </item>
    <item>
      <title>Long</title>
      <!-- No link -->
      <description>&lt;p>Too long&lt;/p>
      </description>
      <category>test</category>
      <pubDate>Sun, 17 Nov 2013 16:56:06 GMT</pubDate>
      <!-- No guid -->
    </item>
    <item>
      <title>The mouf</title>
      <!-- No link -->
      <category>test</category>
      <description>&lt;p>This is just a test&lt;/p>
      </description>
      <pubDate>Sun, 17 Nov 2013 16:56:06 GMT</pubDate>
      <guid>http://mouf/a#guid</guid>
    </item>
  </channel>
</rss>
"""
    
    f1 = feedparser.parse(rss_xml)
    self.ref_and_tags = add_new_references_from_feedparser_entries(web_feed,
                                                                   f1.entries)
    
  def test_references_are_added_with_correct_urls(self):
    references_in_db = list(Reference.objects.all())
    self.assertEqual(3,len(references_in_db))
    ref_urls = [r.url for r in references_in_db]
    self.assertIn("http://www.example.com",ref_urls)
    self.assertIn("http://mouf/a#guid",ref_urls)
    
  def test_references_are_added_with_correct_title(self):
    ref_title = Reference.objects.get(url="http://www.example.com").title
    self.assertEqual("An example bookmark.",ref_title)
    ref_title = Reference.objects.get(url="http://mouf/a#guid").title
    self.assertEqual("The mouf",ref_title)
  
  def test_references_are_added_with_correct_sources(self):
    references_in_db = list(Reference.objects.all())
    self.assertEqual(3,len(references_in_db))
    for ref in references_in_db:
      if ref!=self.source:
        self.assertIn(self.source,ref.sources.all(),ref)

