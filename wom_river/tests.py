# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 4 -*-

import datetime
from django.utils import timezone
from django.utils import simplejson

from django.test import TestCase

from wom_pebbles.models import Reference
from wom_pebbles.models import Source

from wom_river.models import FeedSource
from wom_river.models import URL_MAX_LENGTH
from wom_river.models import ReferenceUserStatus
from wom_river.views import MAX_ITEMS_PER_PAGE

from wom_user.models import UserProfile

from wom_river.tasks import import_feedsources_from_opml

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


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
        self.test_reference = Reference.objects.create(url="http://mouf",title="glop",
                                                       pub_date=self.test_date,source=test_source)
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


class UserRiverViewTest(TestCase):

    def setUp(self):
        # Create 2 users and 3 sources (1 exclusive to each and a
        # shared one) with more references than MAX_ITEM_PER_PAGE
        self.user1 = User.objects.create_user(username="uA",password="pA")
        test_user1_profile = UserProfile.objects.create(user=self.user1)
        self.user2 = User.objects.create_user(username="uB",password="pB")
        test_user2_profile = UserProfile.objects.create(user=self.user2)
        test_date = datetime.datetime.now(timezone.utc)
        s1 = FeedSource.objects.create(xmlURL="http://mouf/rss.xml",last_update_check=test_date,url="http://mouf",name="glop")
        s2 = FeedSource.objects.create(xmlURL="http://bla/rss.xml",last_update_check=test_date,url="http://bla",name="bla")
        s3 = FeedSource.objects.create(xmlURL="http://greuh/rss.xml",last_update_check=test_date,url="http://greuh",name="greuh")
        test_user1_profile.feed_sources.add(s1)
        test_user1_profile.feed_sources.add(s3)
        test_user2_profile.feed_sources.add(s2)
        test_user2_profile.feed_sources.add(s3)
        num_items = MAX_ITEMS_PER_PAGE+1
        for i in range(num_items):
            test_date += datetime.timedelta(hours=1)
            Reference.objects.create(url="http://mouf",title="s1r%d" % i,
                                     pub_date=test_date,source=s1)
            Reference.objects.create(url="http://mouf",title="s2r%d" % i,
                                     pub_date=test_date,source=s2)
            Reference.objects.create(url="http://mouf",title="s3r%d" % i,
                                     pub_date=test_date,source=s3)

    def test_get_html_for_owner_returns_max_items_ordered_newest_first(self):
        """
        Make sure a user can see its river properly ordered
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uA's river
        resp = self.client.get(reverse("wom_river.views.user_river_view",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("wom_river/river.html_dt",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("latest_unread_references", resp.context)
        items = resp.context["latest_unread_references"]
        self.assertGreaterEqual(MAX_ITEMS_PER_PAGE,len(items))
        sourceNames = set(int(ref.title[1]) for ref in items)
        self.assertItemsEqual(sourceNames,(1,3))
        referenceNumbers = [int(r.title[3:]) for r in items]
        self.assertEqual(list(reversed(sorted(referenceNumbers))),referenceNumbers)
        
    def test_get_html_for_non_owner_logged_user_returns_max_items_ordered_newest_first(self):
        """
        Make sure a logged in user can see another user's river.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uB's river
        resp = self.client.get(reverse("wom_river.views.user_river_view",
                                       kwargs={"owner_name":"uB"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("wom_river/river.html_dt",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("latest_unread_references", resp.context)
        items = resp.context["latest_unread_references"]
        self.assertGreaterEqual(MAX_ITEMS_PER_PAGE,len(items))
        sourceNames = set(int(ref.title[1]) for ref in items)
        self.assertItemsEqual(sourceNames,(2,3))
        referenceNumbers = [int(r.title[3:]) for r in items]
        self.assertEqual(list(reversed(sorted(referenceNumbers))),referenceNumbers)
        
    def test_get_html_for_anonymous_returns_max_items_ordered_newest_first(self):
        """
        Make sure an anonymous (ie. not logged in) user can see a user's river.
        """
        # request uA's river without loging in.
        resp = self.client.get(reverse("wom_river.views.user_river_view",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("wom_river/river.html_dt",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("latest_unread_references", resp.context)
        items = resp.context["latest_unread_references"]
        self.assertGreaterEqual(MAX_ITEMS_PER_PAGE,len(items))
        sourceNames = set(int(ref.title[1]) for ref in items)
        self.assertItemsEqual(sourceNames,(1,3))
        referenceNumbers = [int(r.title[3:]) for r in items]
        self.assertEqual(list(reversed(sorted(referenceNumbers))),referenceNumbers)


class UserSieveViewTest(TestCase):

    def setUp(self):
        # Create 2 users and 3 sources (1 exclusive to each and a
        # shared one) with more references than MAX_ITEM_PER_PAGE
        self.user1 = User.objects.create_user(username="uA",password="pA")
        test_user1_profile = UserProfile.objects.create(user=self.user1)
        self.user2 = User.objects.create_user(username="uB",password="pB")
        test_user2_profile = UserProfile.objects.create(user=self.user2)
        test_date = datetime.datetime.now(timezone.utc)
        s1 = FeedSource.objects.create(xmlURL="http://mouf/rss.xml",last_update_check=test_date,url="http://s1",name="glop")
        s2 = FeedSource.objects.create(xmlURL="http://bla/rss.xml",last_update_check=test_date,url="http://s2",name="bla")
        s3 = FeedSource.objects.create(xmlURL="http://greuh/rss.xml",last_update_check=test_date,url="http://s3",name="greuh")
        test_user1_profile.feed_sources.add(s1)
        test_user1_profile.feed_sources.add(s3)
        test_user2_profile.feed_sources.add(s2)
        test_user2_profile.feed_sources.add(s3)
        num_items = MAX_ITEMS_PER_PAGE+1
        for i in range(num_items):
            test_date += datetime.timedelta(hours=1)
            Reference.objects.create(url="http://r1",title="s1r%d" % i,
                                     pub_date=test_date,source=s1)
            Reference.objects.create(url="http://r2",title="s2r%d" % i,
                                     pub_date=test_date,source=s2)
            Reference.objects.create(url="http://r3",title="s3r%d" % i,
                                     pub_date=test_date,source=s3)

    def test_get_html_for_owner_returns_max_items_ordered_oldest_first(self):
        """
        Make sure a user can see its river properly ordered
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uA's river
        resp = self.client.get(reverse("wom_river.views.user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("wom_river/sieve.html_dt",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("user_collection_url", resp.context)
        self.assertIn("oldest_unread_references", resp.context)
        items = resp.context["oldest_unread_references"]
        self.assertGreaterEqual(MAX_ITEMS_PER_PAGE,len(items))
        self.assertEqual((False,),tuple(set([s.has_been_read for s in items])))
        sourceNames = set([int(s.ref.title[1]) for s in items])
        self.assertEqual(sourceNames,set((1,3)))
        referenceNumbers = [int(s.ref.title[3:]) for s in items]
        self.assertEqual(list(sorted(referenceNumbers)),referenceNumbers)
        
    def test_get_html_for_non_owner_logged_user_is_forbidden(self):
        """
        Make sure a logged in user can see another user's river.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uB's river
        resp = self.client.get(reverse("wom_river.views.user_river_sieve",
                                       kwargs={"owner_name":"uB"}))
        self.assertEqual(403,resp.status_code)        
        
    def test_get_html_for_anonymous_redirects_to_login(self):
        """
        Make sure an anonymous (ie. not logged) user can see a user's river.
        """
        # request uA's river without loging in.
        resp = self.client.get(reverse("wom_river.views.user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(302,resp.status_code)
        self.assertRegexpMatches(resp["Location"],
                                 "http://\\w+"
                                 + reverse('django.contrib.auth.views.login')
                                 + "\\?next="
                                 + reverse("wom_river.views.user_river_sieve",
                                           kwargs={"owner_name":"uA"}))
        
    def test_post_json_pick_item_out_of_sieve(self):
        """
        Make sure posting an item as read will remove it from the sieve.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # check presence of r1 reference
        resp = self.client.get(reverse("wom_river.views.user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        num_ref_r1 = [r.ref.url for r in items].count("http://r1")
        self.assertLessEqual(1,num_ref_r1)
        # mark the first reference as read.
        resp = self.client.post(reverse("wom_river.views.user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                simplejson.dumps({"action":"read","references":["http://r1"]}),
                                content_type="application/json")
        self.assertEqual(200,resp.status_code)
        resp_dic = simplejson.loads(resp.content)
        self.assertEqual("read",resp_dic["action"])
        self.assertEqual("success",resp_dic["status"])
        self.assertLessEqual(num_ref_r1,resp_dic["count"])
        # check absence of r1 reference
        resp = self.client.get(reverse("wom_river.views.user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        self.assertEqual(0,[r.ref.url for r in items].count("http://r1"))

    def test_post_json_pick_several_items_out_of_sieve(self):
        """
        Make sure posting a list of items as read will remove them from the sieve.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # check presence of r1 reference
        resp = self.client.get(reverse("wom_river.views.user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        num_ref_r1 = [r.ref.url for r in items].count("http://r1")
        self.assertLessEqual(1,num_ref_r1)
        num_ref_r3 = [r.ref.url for r in items].count("http://r3")
        self.assertLessEqual(1,num_ref_r3)
        # mark the first reference as read.
        resp = self.client.post(reverse("wom_river.views.user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                simplejson.dumps({"action":"read",
                                                  "references":["http://r1","http://r3"]}),
                                content_type="application/json")
        self.assertEqual(200,resp.status_code)
        resp_dic = simplejson.loads(resp.content)
        self.assertEqual("read",resp_dic["action"])
        self.assertEqual("success",resp_dic["status"])
        self.assertLessEqual(num_ref_r1+num_ref_r3,resp_dic["count"])
        # check absence of r1 reference
        resp = self.client.get(reverse("wom_river.views.user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        self.assertEqual(0,[r.ref.url for r in items].count("http://r1"))
        self.assertEqual(0,[r.ref.url for r in items].count("http://r3"))        

    def test_post_malformed_json_returns_error(self):
        """
        Make sure when the json is malformed an error that is not a server error is returned.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # mark a of uB reference as read.
        resp = self.client.post(reverse("wom_river.views.user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                "action=read,references=(http://r1)",
                                content_type="application/json")
        self.assertEqual(400,resp.status_code)

    def test_post_json_for_non_owner_logged_user_is_forbidden(self):
        """
        Make sure when the json is malformed an error that is not a server error is returned.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # mark a of uB reference as read.
        resp = self.client.post(reverse("wom_river.views.user_river_sieve",
                                        kwargs={"owner_name":"uB"}),
                                simplejson.dumps({"action":"read","references":["http://r2"]}),
                                content_type="application/json")
        self.assertEqual(403,resp.status_code)

    def test_post_json_for_anonymous_redirects(self):
        """
        Make sure an anonymous (ie. not logged) user can see a user's river.
        """
        resp = self.client.post(reverse("wom_river.views.user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                simplejson.dumps({"action":"read","references":["http://r1"]}),
                                content_type="application/json")
        self.assertEqual(302,resp.status_code)

        
class UserSourcesViewTest(TestCase):

    def setUp(self):
        # Create 2 users and 3 feed sources (1 exclusive to each and a
        # shared one) and 3 non-feed sources.
        self.user1 = User.objects.create_user(username="uA",password="pA")
        test_user1_profile = UserProfile.objects.create(user=self.user1)
        self.user2 = User.objects.create_user(username="uB",password="pB")
        test_user2_profile = UserProfile.objects.create(user=self.user2)
        test_date = datetime.datetime.now(timezone.utc)
        fs1 = FeedSource.objects.create(xmlURL="http://mouf/rss.xml",last_update_check=test_date,url="http://mouf",name="f1")
        fs2 = FeedSource.objects.create(xmlURL="http://bla/rss.xml",last_update_check=test_date,url="http://bla",name="f2")
        fs3 = FeedSource.objects.create(xmlURL="http://greuh/rss.xml",last_update_check=test_date,url="http://greuh",name="f3")
        test_user1_profile.feed_sources.add(fs1)
        test_user1_profile.feed_sources.add(fs3)
        test_user2_profile.feed_sources.add(fs2)
        test_user2_profile.feed_sources.add(fs3)
        test_user1_profile.sources.add(fs1)
        test_user1_profile.sources.add(fs3)
        test_user2_profile.sources.add(fs2)
        test_user2_profile.sources.add(fs3)
        # also add plain sources
        s1 = Source.objects.create(url="http://s1",name="s1")
        s2 = Source.objects.create(url="http://s2",name="s2")
        s3 = Source.objects.create(url="http://s3",name="s3")
        test_user1_profile.sources.add(s1)
        test_user1_profile.sources.add(s3)
        test_user2_profile.sources.add(s2)
        test_user2_profile.sources.add(s3)

    def test_get_html_for_owner_returns_separate_source_and_feed(self):
        """
        Make sure a user can see its sources in two categories.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uA's river
        resp = self.client.get(reverse("wom_river.views.user_river_sources",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("wom_river/river_sources.html_dt",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("syndicated_sources", resp.context)
        self.assertIn("referenced_sources", resp.context)
        items = resp.context["referenced_sources"]
        sourceNames = set([int(s.name[1]) for s in items])
        self.assertEqual(sourceNames,set((1,3)))
        sourceTypes = set([s.name[0] for s in items])
        self.assertEqual(set(("s",)),sourceTypes)
        feed_items = resp.context["syndicated_sources"]
        feedNames = set([int(s.name[1]) for s in feed_items])
        self.assertEqual(feedNames,set((1,3)))
        feedTypes = set([s.name[0] for s in feed_items])
        self.assertEqual(set(("f",)),feedTypes)
        
    def test_get_html_for_non_owner_logged_user_returns_all_sources(self):
        """
        Make sure a logged in user can see another user's sources.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uB's river
        resp = self.client.get(reverse("wom_river.views.user_river_sources",
                                       kwargs={"owner_name":"uB"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("wom_river/river_sources.html_dt",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("syndicated_sources", resp.context)
        self.assertIn("referenced_sources", resp.context)
        items = resp.context["referenced_sources"]
        sourceNames = set([int(s.name[1]) for s in items])
        self.assertEqual(sourceNames,set((2,3)))
        sourceTypes = set([s.name[0] for s in items])
        self.assertEqual(set(("s",)),sourceTypes)
        feed_items = resp.context["syndicated_sources"]
        feedNames = set([int(s.name[1]) for s in feed_items])
        self.assertEqual(feedNames,set((2,3)))
        feedTypes = set([s.name[0] for s in feed_items])
        self.assertEqual(set(("f",)),feedTypes)
        
    def test_get_html_for_anonymous_returns_all_sources(self):
        """
        Make sure an anonymous user can see users' sources.
        """
        # request uA's river
        resp = self.client.get(reverse("wom_river.views.user_river_sources",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("wom_river/river_sources.html_dt",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("syndicated_sources", resp.context)
        self.assertIn("referenced_sources", resp.context)
        items = resp.context["referenced_sources"]
        sourceNames = set([int(s.name[1]) for s in items])
        self.assertEqual(sourceNames,set((1,3)))
        sourceTypes = set([s.name[0] for s in items])
        self.assertEqual(set(("s",)),sourceTypes)
        feed_items = resp.context["syndicated_sources"]
        feedNames = set([int(s.name[1]) for s in feed_items])
        self.assertEqual(feedNames,set((1,3)))
        feedTypes = set([s.name[0] for s in feed_items])
        self.assertEqual(set(("f",)),feedTypes)

        
class ImportFeedSourcesFromOPMLTaskTest(TestCase):
    
    def setUp(self):
        # Create 2 users but only create sources for one of them.
        self.user1 = User.objects.create_user(username="uA",password="pA")
        # self.user1_profile = UserProfile.objects.create(user=self.user1)
        # self.user2 = User.objects.create_user(username="uB",password="pB")
        # self.user2_profile = UserProfile.objects.create(user=self.user2)
        test_date = datetime.datetime.now(timezone.utc)
        self.fs1 = FeedSource.objects.create(xmlURL="http://mouf/rss.xml",last_update_check=test_date,url="http://mouf",name="f1")
        self.fs3 = FeedSource.objects.create(xmlURL="http://greuh/rss.xml",last_update_check=test_date,url="http://greuh",name="f3")
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

