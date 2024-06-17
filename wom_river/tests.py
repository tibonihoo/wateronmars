# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2013-2019 Thibauld Nion
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

from datetime import datetime, timedelta
from django.utils import timezone

import feedparser

from django.test import TestCase

from wom_pebbles.models import Reference

from wom_river.models import (
    WebFeed,
    URL_MAX_LENGTH,
    WebFeedCollation
    )

from wom_river.tasks import (
    import_feedsources_from_opml,
    add_new_references_from_parsed_feed,
    generate_collated_content,
    yield_collated_reference,
    generate_collations,
    )

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



class AddReferencesFromFeedParserEntriesTaskTest(TestCase):

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
    self.ref_and_tags = add_new_references_from_parsed_feed(web_feed, f1.entries, None)

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

class AddReferencesFromFeedParserTaskOnBrokenFeedTest(TestCase):

  def setUp(self):
    date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
      url="http://example.com",
      title="Test Source",
      pub_date=date)
    self.web_feed  = WebFeed.objects.create(
        xmlURL="http://mouf/rss.xml",
        source=self.source,
        last_update_check=\
        datetime.utcfromtimestamp(0)\
        .replace(tzinfo=timezone.utc))
    # RSS from a source that already has a mapping
    self.rss_xml = """\
<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Source</title>
    <link>http://example.com/test_source</link>
    <description>A RSS test source</description>
    <pubDate>Sun, 17 Nov 2013 19:08:15 GMT</pubDate>
    <lastBuildDate>Sun, 18 Nov 2013 20:18:32 GMT</lastBuildDate>
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
      <title>The mouf date</title>
      <!-- No link -->
      <category>test</category>
      <description>&lt;p>This is just a test&lt;/p>
      </description>
      <pubDate>Sun, 17 Nov 2013 16:56:06 GMT</pubDate>
      <guid>http://mouf/a#guid</guid>
    </item>
    <item>
      <title>The mouf</title>
      <!-- No link -->
      <category>test</category>
      <description>&lt;p>This is just a test&lt;/p>
      </description>
      <!-- No pubDate -->
      <guid>http://mouf/b#guid</guid>
    </item>
    <item>
      <title>The helpless</title>
      <!-- No link -->
      <category>test</category>
      <description>&lt;p>This is just a test&lt;/p>
      </description>
      <!-- No pubDate -->
      <guid isPermaLink="false">12</guid>
    </item>
    <item>
      <title>The art</title>
      <!-- No link but an enclosure -->
      <enclosure url="https://imgs.mouf/2023/11/17/amused.png" type="image/png" size="42"/>
      <category>test</category>
      <description>&lt;p>This is just a test&lt;/p>
      </description>
      <!-- No pubDate -->
      <guid isPermaLink="false">123</guid>
    </item>
  </channel>
</rss>
"""

    f1 = feedparser.parse(self.rss_xml)
    self.default_date = date
    print(f1.entries)
    self.ref_and_tags = add_new_references_from_parsed_feed(
        self.web_feed,
        f1.entries,
        self.default_date)

  def test_references_are_added_with_correct_urls(self):
    references_in_db = list(Reference.objects.all())
    self.assertEqual(5, len(references_in_db))
    ref_urls = [r.url for r in references_in_db]
    self.assertIn("http://www.example.com", ref_urls)
    self.assertIn("http://mouf/a#guid", ref_urls)
    self.assertIn("http://mouf/b#guid", ref_urls)
    self.assertIn("https://imgs.mouf/2023/11/17/amused.png", ref_urls)

  def test_references_are_added_with_correct_title(self):
    ref_title = Reference.objects.get(url="http://www.example.com").title
    self.assertEqual("An example bookmark.",ref_title)
    ref_title = Reference.objects.get(url="http://mouf/a#guid").title
    self.assertEqual("The mouf date",ref_title)
    ref_title = Reference.objects.get(url="http://mouf/b#guid").title
    self.assertEqual("The mouf",ref_title)
    ref_title = Reference.objects.get(url="https://imgs.mouf/2023/11/17/amused.png").title
    self.assertEqual("The art",ref_title)

  def test_references_are_added_with_correct_sources(self):
    references_in_db = list(Reference.objects.all())
    self.assertEqual(5,len(references_in_db))
    for ref in references_in_db:
      if ref!=self.source:
        self.assertIn(self.source,ref.sources.all(),ref)

  def test_references_are_added_with_default_date(self):
    references_in_db = list(Reference.objects.all())
    print(references_in_db)
    self.assertEqual(5,len(references_in_db))
    for r in references_in_db:
      if r.title == "The mouf date":
        continue
      self.assertEqual(self.default_date.utctimetuple()[:6],
                       r.pub_date.utctimetuple()[:6],
                       r.title)

  def test_dates_not_updated_even_for_dateless_items(self):
    references_in_db = list(Reference.objects.all())
    self.assertEqual(5,len(references_in_db))
    first_dates = set(r.pub_date for r in references_in_db)
    f2 = feedparser.parse(self.rss_xml)
    new_default_date = self.default_date + timedelta(days=1)
    self.ref_and_tags = add_new_references_from_parsed_feed(
        self.web_feed,
        f2.entries,
        new_default_date)
    references_in_db = list(Reference.objects.all())
    self.assertEqual(5,len(references_in_db))
    new_dates = set(r.pub_date for r in references_in_db)
    self.assertEqual(first_dates, new_dates)


class WebFeedCollationModelTest(TestCase):

  def setUp(self):
    self.date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
        url="http://mouf",
        pub_date=self.date)
    self.feed = WebFeed.objects.create(
        xmlURL="http://mouf/bla.xml",
        last_update_check=self.date,
        source=self.source)
    self.collation = WebFeedCollation.objects.create(
        feed=self.feed,
        last_completed_collation_date=datetime.min.replace(tzinfo=timezone.utc))

  def test_construction_defaults(self):
    """
    This tests just makes it possible to double check that a
    change in the default is voluntary.
    """
    self.assertEqual(self.feed, self.collation.feed)
    self.assertEqual(0, len(self.collation.references.all()))

  def test_take(self):
    date = self.date + timedelta(days=1)
    r = Reference.objects.create(url="http://mouf/1",
                                 pub_date=date)
    self.collation.take(r)
    taken_refs = list(self.collation.references.all())
    self.assertEqual(1, len(taken_refs))
    self.assertEqual(r, taken_refs[0])

  def test_take_skip_dates_equal_to_latest_flushed_refs(self):
    date = self.date + timedelta(days=1)
    r = Reference.objects.create(url="http://mouf/1",
                                 pub_date=date)
    self.collation.take(r)
    # Take date in the reference's past to be sure the
    # completion date is not taken into account
    completion_date = date + timedelta(days=-1)
    self.collation.flush(completion_date)
    self.assertEqual(0, len(self.collation.references.all()))
    r2 = Reference.objects.create(url="http://mouf/2",
                                  pub_date=date)
    self.collation.take(r2)
    self.assertEqual(0, len(self.collation.references.all()))

  def test_flush_then_references_is_empty(self):
    date = self.date + timedelta(days=1)
    r = Reference.objects.create(url="http://mouf/1",
                                 pub_date=date)
    self.collation.take(r)
    completion_date = date + timedelta(days=1)
    self.collation.flush(completion_date)
    self.assertEqual(0, len(self.collation.references.all()))
    self.assertEqual(completion_date, self.collation.last_completed_collation_date)
    self.assertEqual(date, self.collation.latest_reference_flushed)


def remove_whitespaces(s):
  return "".join(s.split())

class GenerateCollatedContentTaskTest(TestCase):

  def test_given_2_references_sequentially_paste_their_titles_and_descriptions(self):
    date1 = datetime.now(timezone.utc)
    title1 = "Hop 1"
    url1 = "http://mouf/1"
    desc1 = "<b>glop</b> bop."
    r1 = Reference.objects.create(url=url1,
                                  title=title1,
                                  description=desc1,
                                  pub_date=date1)
    date2 = date1 + timedelta(days=2)
    title2 = "Arf 2"
    url2 = "http://mouf/2"
    desc2 = "bip <i>bli</i>"
    r2 = Reference.objects.create(url=url2,
                                  title=title2,
                                  description=desc2,
                                  pub_date=date2)
    res = generate_collated_content([r1, r2])
    expected_res = f"""\
<h2><a href='{url1}'>{title1}</a></h2>
{desc1}
<br/>
<h2><a href='{url2}'>{title2}</a></h2>
{desc2}
<br/>"""
    self.assertEqual(remove_whitespaces(expected_res),
                     remove_whitespaces(res))


class YieldCollatedReferencesTaskTest(TestCase):

  def setUp(self):
    self.date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
        url="http://mouf",
        pub_date=self.date)
    self.parent_path = "wom-tests:/mouf/glop"
    self.feed = WebFeed.objects.create(
        xmlURL="http://mouf/bla.xml",
        last_update_check=self.date,
        source=self.source)
    self.collation = WebFeedCollation.objects.create(
        feed=self.feed,
        last_completed_collation_date=datetime.min.replace(tzinfo=timezone.utc))
    self.min_num_ref_target = 2
    self.max_num_ref_target = 20
    self.timeout = timedelta(days=2)

  def _add_reference_1(self):
    title1 = "Hop 1"
    url1 = "http://mouf/1"
    desc1 = "<b>glop</b> bop."
    date1 = datetime.utcfromtimestamp(10).replace(tzinfo=timezone.utc)
    r1 = Reference.objects.create(url=url1,
                                  title=title1,
                                  description=desc1,
                                  pub_date=date1)
    r1.save()
    self.collated_content_r1 = f"""\
<h2><a href='{url1}'>{title1}</a></h2>
{desc1}
<br/>"""
    self.collation.references.add(r1)
    return r1

  def _add_reference_2(self):
    title2 = "Arf 2"
    url2 = "http://mouf/2"
    desc2 = "bip <i>bli</i>"
    date2 = datetime.utcfromtimestamp(20).replace(tzinfo=timezone.utc)
    r2 = Reference.objects.create(url=url2,
                                  title=title2,
                                  description=desc2,
                                  pub_date=date2)
    r2.save()
    self.collated_content_r2 = f"""\
<h2><a href='{url2}'>{title2}</a></h2>
{desc2}
<br/>"""
    self.collation.references.add(r2)
    return r2

  def test_given_empty_collation_yields_empty_results(self):
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        self.min_num_ref_target,
                                        self.max_num_ref_target,
                                        self.timeout,
                                        datetime.utcnow()))
    self.assertEqual(0, len(res))

  def test_given_0_ref_target_does_not_output_empty_content_ref(self):
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        0,
                                        self.max_num_ref_target,
                                        self.timeout,
                                        datetime.utcnow()))
    self.assertEqual(0, len(res))

  def test_given_ref_added_and_processing_before_timeout_no_collation_returned(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 1
    self._add_reference_1()
    processing_date = last_completion_date + timeout - timedelta(days=1)
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(0, len(res))

  def test_given_2refs_added_and_processing_after_timeout_returns_collation(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 1
    self._add_reference_1()
    self._add_reference_2()
    processing_date = last_completion_date + timeout + timedelta(days=1)
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(1, len(res))
    expected_res_ref_desc = f"""\
{self.collated_content_r1}
{self.collated_content_r2}"""
    self.assertEqual(remove_whitespaces(expected_res_ref_desc),
                     remove_whitespaces(res[0].description))

  def test_given_too_few_refs_added_processing_after_timeout_returns_no_collation(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 2
    self._add_reference_1()
    processing_date = last_completion_date + timeout + timedelta(days=1)
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(0, len(res))

  def test_given_too_few_ref_processing_long_enough_after_timeout_returns_collation(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 2
    self._add_reference_1()
    processing_date = last_completion_date + 2 * timeout
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(1, len(res))
    self.assertEqual(remove_whitespaces(self.collated_content_r1),
                     remove_whitespaces(res[0].description))
    from bs4 import BeautifulSoup

  def test_given_same_processing_date_avoid_creating_duplicate_ref(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 1
    processing_date = last_completion_date + timeout + timedelta(days=1)
    r1 = self._add_reference_1()
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(1, len(res))
    # Cheating a bit to force processing of the collation with a same processing_date.
    self.collation.last_completed_collation_date = last_completion_date
    self.collation.references.add(r1)
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(0, len(res))

  def test_given_some_ref_and_new_processing_date_create_second_collation(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 1
    processing_date = last_completion_date + timeout + timedelta(days=1)
    r1 = self._add_reference_1()
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(1, len(res))
    self.collation.references.add(r1)
    processing_date = processing_date + timeout + timedelta(days=1)
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(1, len(res))

  def test_given_more_refs_than_max_accumulate_collations_happens(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 1
    max_num_ref_target = 10
    self._add_reference_1()
    processing_date = last_completion_date
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(0, len(res))
    for i in range(100):
        title = f"Too {i}"
        desc = "much"
        date = datetime.utcfromtimestamp(20).replace(tzinfo=timezone.utc)
        r = Reference.objects.create(url=f"http://more/{i}",
                                    title=title,
                                    description=desc,
                                    pub_date=date)
        self.collation.references.add(r)
    res = list(yield_collated_reference(self.parent_path,
                                        self.feed,
                                        self.collation,
                                        min_num_ref_target,
                                        self.max_num_ref_target,
                                        timeout,
                                        processing_date))
    self.assertEqual(1, len(res))


class GenerateCollationsTaskTest(TestCase):

  def setUp(self):
    self.date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
        url="http://mouf",
        pub_date=self.date)
    self.parent_path = "wom-tests:/mouf/glop"
    self.feed = WebFeed.objects.create(
        xmlURL="http://mouf/bla.xml",
        last_update_check=self.date,
        source=self.source)
    self.collation = WebFeedCollation.objects.create(
        feed=self.feed,
        last_completed_collation_date=datetime.min.replace(tzinfo=timezone.utc))
    self.min_num_ref_target = 2
    self.timeout = timedelta(days=2)
    self.r1 = self._add_reference_1()
    self.r2 = self._add_reference_2()

  def _add_reference_1(self):
    title1 = "Hop 1"
    url1 = "http://mouf/1"
    desc1 = "<b>glop</b> bop."
    date1 = datetime.utcfromtimestamp(10).replace(tzinfo=timezone.utc)
    r1 = Reference.objects.create(url=url1,
                                  title=title1,
                                  description=desc1,
                                  pub_date=date1)
    r1.save()
    self.collated_content_r1 = f"""\
<h2><a href='{url1}'>{title1}</a></h2>
{desc1}
<br/>"""
    return r1

  def _add_reference_2(self):
    title2 = "Arf 2"
    url2 = "http://mouf/2"
    desc2 = "bip <i>bli</i>"
    date2 = datetime.utcfromtimestamp(20).replace(tzinfo=timezone.utc)
    r2 = Reference.objects.create(url=url2,
                                  title=title2,
                                  description=desc2,
                                  pub_date=date2)
    r2.save()
    self.collated_content_r2 = f"""\
<h2><a href='{url2}'>{title2}</a></h2>
{desc2}
<br/>"""
    return r2

  def test_no_collation_because_too_early(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 1
    max_num_ref_target = 10
    processing_date = last_completion_date + timeout - timedelta(days=1)
    res = list(generate_collations(self.parent_path,
                                   self.feed,
                                   self.collation,
                                   [self.r1],
                                   min_num_ref_target,
                                   max_num_ref_target,
                                   timeout,
                                   processing_date))
    self.assertEqual(0, len(res))

  def test_collation_after_timeout(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 1
    max_num_ref_target = 10
    processing_date = last_completion_date + timeout + timedelta(days=1)
    res = list(generate_collations(self.parent_path,
                                   self.feed,
                                   self.collation,
                                   [self.r1],
                                   min_num_ref_target,
                                   max_num_ref_target,
                                   timeout,
                                   processing_date))
    self.assertEqual(1, len(res))

  def test_no_collation_because_too_few_refs(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 2
    max_num_ref_target = 20
    processing_date = last_completion_date + timeout + timedelta(days=1)
    res = list(generate_collations(self.parent_path,
                                   self.feed,
                                   self.collation,
                                   [self.r1],
                                   min_num_ref_target,
                                   max_num_ref_target,
                                   timeout,
                                   processing_date))
    self.assertEqual(0, len(res))

  def test_collation_on_last_ref(self):
    last_completion_date = self.collation.last_completed_collation_date
    timeout = timedelta(days=15)
    min_num_ref_target = 2
    max_num_ref_target = 20
    processing_date = last_completion_date + timeout + timedelta(days=1)
    res = list(generate_collations(self.parent_path,
                                   self.feed,
                                   self.collation,
                                   [self.r1, self.r2],
                                   min_num_ref_target,
                                   max_num_ref_target,
                                   timeout,
                                   processing_date))
    self.assertEqual(1, len(res))
