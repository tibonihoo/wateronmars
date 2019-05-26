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
from django.utils import simplejson

from django.core.urlresolvers import reverse

from django.test import TestCase

from wom_pebbles.models import Reference
from wom_river.models import WebFeed

from wom_user.models import UserProfile
from wom_user.models import UserBookmark

from wom_user.tasks import import_user_bookmarks_from_ns_list

from wom_classification.models import Tag
from wom_classification.models import get_item_tag_names
from wom_classification.models import set_item_tag_names

from django.contrib.auth.models import User


class UserBookmarkModelTest(TestCase):

  def setUp(self):
    self.date = datetime.now(timezone.utc)
    self.reference = Reference.objects.create(url="http://mouf",
                                              title="glop",
                                              pub_date=self.date)
    self.user = User.objects.create(username="name")
    
  def test_construction_defaults(self):
    """
    This tests just makes it possible to double check that a
    change in the default is voluntary.
    """
    b = UserBookmark.objects.create(owner=self.user,
                    reference=self.reference,
                    saved_date=self.date)
    self.assertFalse(b.is_public)

  def test_get_public_sources(self):
    source = Reference.objects.create(url="http://src",
                                      title="src",
                                      pub_date=self.date)
    b = UserBookmark.objects.create(owner=self.user,
                                    reference=self.reference,
                                    saved_date=self.date)
    b.reference.sources.add(source)
    userprofile = UserProfile.objects.create(owner=self.user)
    userprofile.sources.add(source)
    self.assertEqual([],list(b.get_public_sources()))
    userprofile.public_sources.add(source)
    self.assertEqual([source],list(b.get_public_sources()))
  
  def test_get_sources(self):
    source = Reference.objects.create(url="http://src",
                                      title="src",
                                      pub_date=self.date)
    b = UserBookmark.objects.create(owner=self.user,
                                    reference=self.reference,
                                    saved_date=self.date)
    b.reference.sources.add(source)
    userprofile = UserProfile.objects.create(owner=self.user)
    userprofile.sources.add(source)
    self.assertEqual([source],list(b.get_sources()))

  def test_set_public(self):
    source = Reference.objects.create(url="http://src",
                                      title="src",
                                      pub_date=self.date)
    b = UserBookmark.objects.create(owner=self.user,
                                    reference=self.reference,
                                    saved_date=self.date)
    b.reference.sources.add(source)
    userprofile = UserProfile.objects.create(owner=self.user)
    userprofile.sources.add(source)
    self.assertNotIn(source,userprofile.public_sources.all())
    b.set_public()
    self.assertIn(source,userprofile.public_sources.all())    
    self.assertIn(source,userprofile.sources.all())    

  def test_set_private_when_public(self):
    source = Reference.objects.create(url="http://src",
                                      title="src",
                                      pub_date=self.date)
    b = UserBookmark.objects.create(owner=self.user,
                                    reference=self.reference,
                                    saved_date=self.date)
    b.reference.sources.add(source)
    userprofile = UserProfile.objects.create(owner=self.user)
    userprofile.sources.add(source)
    userprofile.public_sources.add(source)
    b.is_public = True
    b.set_private()
    self.assertNotIn(source,userprofile.public_sources.all())
    self.assertIn(source,userprofile.sources.all())
    
  def test_set_private_when_has_feed(self):
    source = Reference.objects.create(url="http://src",
                                      title="src",
                                      pub_date=self.date)
    feed = WebFeed.objects.create(xmlURL="http://barf/bla.xml",
                                  last_update_check=self.date,
                                  source=source)
    b = UserBookmark.objects.create(owner=self.user,
                                    reference=self.reference,
                                    saved_date=self.date)
    b.reference.sources.add(source)
    userprofile = UserProfile.objects.create(owner=self.user)
    userprofile.web_feeds.add(feed)
    userprofile.sources.add(source)
    userprofile.public_sources.add(source)
    b.is_public = True
    b.set_private()
    # Since the feed exists: the source is still public !
    self.assertIn(source,userprofile.public_sources.all())
    self.assertIn(source,userprofile.sources.all())
    

# # TODO: test ordering and paging !

class UserBookmarkAddTestMixin:
  """Mixin implementing the common tests for the Form and the REST API
  of bookmark addition.
  """

  def add_request(self,url,optionsDict):
    """
    Returns the response that can be received from the input url.
    """
    raise NotImplementedError("This method should be reimplemented")
  
  def setUp(self):
    date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
      url=u"http://mouf",
      title=u"mouf",
      pub_date=date)
    reference = Reference.objects.create(
      url=u"http://mouf/a",
      title=u"glop",
      pub_date=date)
    reference.sources.add(self.source)
    reference_private = Reference.objects.create(
      url=u"http://mouf/p",
      title=u"nop",
      pub_date=date)
    reference_private.sources.add(self.source)
    reference_b = Reference.objects.create(
      url=u"http://mouf/b",
      title=u"paglop",
      pub_date=date)
    reference_b.sources.add(self.source)
    self.user = User.objects.create_user(username="uA",
                                         password="pA")
    p = UserProfile.objects.create(owner=self.user)
    p.sources.add(self.source)
    self.bkm = UserBookmark.objects.create(
      owner=self.user,
      reference=reference,
      saved_date=date,
      is_public=True)
    self.bkm_private = UserBookmark.objects.create(
      owner=self.user,
      reference=reference_private,
      saved_date=date)
    self.other_user = User.objects.create_user(username="uB",
                                               password="pB")
    self.bkm_b = UserBookmark.objects.create(
      owner=self.other_user,
      reference=reference_b,
      saved_date=date,
      is_public=True)  
    
  def test_add_new_item_is_added(self):
    """
    Posting a bookmark will add it to the user's collection.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": u"http://new/mouf",
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": u"http://glop",
                  "source_title": u"new name",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(3,resp.context["user_bookmarks"].paginator.count)
    items = resp.context["user_bookmarks"]
    new_b_candidates = [b for b in items \
                        if b.reference.url==u"http://new/mouf"]
    self.assertEqual(1, len(new_b_candidates))
    new_b = new_b_candidates[0]
    self.assertEqual(u"mouf",new_b.comment)
    self.assertEqual(u"new title",new_b.reference.title)
    self.assertEqual(1,len(new_b.reference.sources.all()))
    new_b_src = new_b.reference.sources.all()[0]
    self.assertEqual(u"http://glop",new_b_src.url)
    self.assertEqual(u"new name",new_b_src.title)
    
    
  def test_add_new_item_is_added_without_source(self):
    """
    Posting a bookmark without providing a source will
    add the bookmark correctly anyway.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": u"http://new/mouf",
                  "title": u"new title",
                  "comment": u"mouf",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(3,resp.context["user_bookmarks"].paginator.count)
    items = resp.context["user_bookmarks"]
    new_b_candidates = [b for b in items \
                        if b.reference.url==u"http://new/mouf"]
    self.assertEqual(1, len(new_b_candidates))
    new_b = new_b_candidates[0]
    self.assertEqual(u"mouf",new_b.comment)
    self.assertEqual(u"new title",new_b.reference.title)
    self.assertEqual(1,len(new_b.reference.sources.all()))
    new_b_src = new_b.reference.sources.all()[0]
    self.assertEqual(u"http://new",new_b_src.url)
    self.assertEqual(u"new",new_b_src.title)

  def test_add_new_item_is_added_with_url_only(self):
    """
    Posting a bookmark without providing anything but a url
    add the bookmark correctly anyway.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    # mark the first reference as read.
    resp = self.add_request("uA", { "url": u"http://new/mouf"})
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(3,resp.context["user_bookmarks"].paginator.count)
    items = resp.context["user_bookmarks"]
    new_b_candidates = [b for b in items \
                        if b.reference.url==u"http://new/mouf"]
    self.assertEqual(1, len(new_b_candidates))
    new_b = new_b_candidates[0]
    self.assertEqual(u"",new_b.comment)
    self.assertEqual(u"new/mouf",new_b.reference.title)
    self.assertEqual(1,len(new_b.reference.sources.all()))
    new_b_src = new_b.reference.sources.all()[0]
    self.assertEqual(u"http://new",new_b_src.url)
    self.assertEqual(u"new",new_b_src.title)
    
  def test_add_new_item_is_added_with_existing_source_url(self):
    """
    Posting a bookmark with a source url that matches an
    exiting one, will associate the new bookmark with the existing
    source.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": u"http://new/mouf",
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": self.source.url,
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(3,resp.context["user_bookmarks"].paginator.count)
    items = resp.context["user_bookmarks"]
    self.assertIn(u"http://new/mouf",[b.reference.url for b in items])
    self.assertIn(u"mouf",[b.comment for b in items \
                           if b.reference.url==u"http://new/mouf"])
    self.assertEqual(self.source,
                     Reference\
                     .objects.get(url=u"http://new/mouf").sources.get())

  def test_add_new_item_is_added_with_existing_url(self):
    """
    Posting a bookmark with a url for which a bookmark already
    exists will update the bookmark's title and description.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": self.bkm.reference.url,
                  "title": u"new title",
                  "comment": u"mouf",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    self.assertIn(self.bkm.reference.url,
            [b.reference.url for b  in resp.context["user_bookmarks"]])
    self.assertEqual(1,
             Reference.objects\
               .filter(url=self.bkm.reference.url).count())
    r = Reference.objects.get(url=self.bkm.reference.url)
    self.assertEqual(self.source.url,r.sources.get().url)
    # The ref info hasn't changed
    self.assertEqual(u"glop",r.title)
    self.assertEqual(u"",r.description)
    self.assertEqual(u"new title: mouf",
                     UserBookmark.objects.get(reference=r).comment)
    
  def test_add_new_item_is_added_with_existing_url_other_source(self):
    """
    Posting a bookmark with a url for which a bookmark already
    exists will update the bookmark's title, description and source.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": self.bkm.reference.url,
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": u"http://barf",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    self.assertIn(self.bkm.reference.url,
            [b.reference.url for b  in resp.context["user_bookmarks"]])
    self.assertEqual(1,
             Reference.objects\
               .filter(url=self.bkm.reference.url).count())
    r = Reference.objects.get(url=self.bkm.reference.url)
    # The source has not changed
    self.assertEqual(u"http://mouf",r.sources.get().url)
    # The ref info has not changed
    self.assertEqual(u"glop",r.title)
    self.assertEqual(u"",r.description)
    self.assertEqual(u"new title: mouf",
                     UserBookmark.objects.get(reference=r).comment)
    
  def test_add_new_item_is_added_with_existing_url_same_source(self):
    """
    Posting a bookmark with a url for which a bookmark already
    exists will update the bookmark's title, description and
    source's name if necessary.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": self.bkm.reference.url,
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": self.source.url,
                  "source_title": u"new name",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    self.assertIn(self.bkm.reference.url,
            [b.reference.url for b  in resp.context["user_bookmarks"]])
    self.assertEqual(1,
             Reference.objects\
               .filter(url=self.bkm.reference.url).count())
    r = Reference.objects.get(url=self.bkm.reference.url)
    self.assertEqual(self.source.url,r.sources.get().url)
    # The source name has not changed
    self.assertEqual(u"mouf",r.sources.get().title)
    # The ref info has not changed
    self.assertEqual(u"glop",r.title)
    self.assertEqual(u"",r.description)
    self.assertEqual(u"new title: mouf",
                     UserBookmark.objects.get(reference=r).comment)
  
  def test_add_new_item_to_other_user_fails(self):
    """
    Posting a bookmark to another user's collection fails.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # mark the first reference as read.
    self.add_request("uB",
             { "url": u"http://new/mouf",
               "title": u"new title",
               "comment": u"mouf",
               "source_url": u"http://glop",
               "source_title": u"new name",
               },
             expectedStatusCode=403)
    
  def test_add_new_item_with_same_url_as_its_sources_succeeds(self):
    """Posting a bookmark by giving the same url for the source and for
    the bookmark should succeed anyway.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # mark the first reference as read.
    self.add_request("uA",
             { "url": u"http://samesame",
               "title": u"same title",
               "comment": u"same",
               "source_url": u"http://samesame",
               "source_title": u"same title",
               })
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    new_item_candidates = [b.reference for b in resp.context["user_bookmarks"] \
                           if b.reference.url == u"http://samesame"]
    self.assertEqual(1,len(new_item_candidates))
    new_item_reference = new_item_candidates[0]
    self.assertEqual(0,len(new_item_reference.sources.all()))
    

class UserCollectionViewTest(TestCase,UserBookmarkAddTestMixin):

  def setUp(self):
    UserBookmarkAddTestMixin.setUp(self)
  
  def add_request(self,username,optionsDict,expectedStatusCode=200):
    """
    Send the request as a JSON loaded POST.
    """
    resp = self.client.post(reverse("wom_user.views.user_collection",
                    kwargs={"owner_name":username}),
                simplejson.dumps(optionsDict),
                content_type="application/json")
    self.assertEqual(expectedStatusCode,resp.status_code)
    return resp
  
  def test_get_html_owner_returns_all(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    # request uA's collection
    resp = self.client.get(
      reverse("wom_user.views.user_collection",
          kwargs={"owner_name":"uA"}))
    self.assertEqual(200,resp.status_code)
    self.assertIn("collection.html",
            [t.name for t in resp.templates])
    self.assertIn("owner_name", resp.context)
    self.assertEqual("uA", resp.context["owner_name"])
    self.assertIn(u"user_bookmarks", resp.context)
    self.assertIn(u"num_bookmarks", resp.context)
    self.assertIn(u"collection_url", resp.context)
    self.assertIn(u"collection_add_bookmarklet", resp.context)
    self.assertEqual(2,resp.context["user_bookmarks"].paginator.count)
    self.assertEqual(2,len(resp.context["user_bookmarks"]))
    self.assertEqual(set([self.bkm,self.bkm_private]),
                     set(resp.context["user_bookmarks"]))
    # test additional attribute
    self.assertNotIn(False,[hasattr(b,"get_tag_names") \
                            for b in resp.context["user_bookmarks"]])
  
  def test_get_html_non_owner_logged_in_user_returns_all(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    # request uB's collection
    resp = self.client.get(
      reverse("wom_user.views.user_collection",
          kwargs={"owner_name":"uB"}))
    self.assertEqual(200,resp.status_code)
    self.assertIn("collection.html",
            [t.name for t in resp.templates])
    self.assertIn(u"user_bookmarks", resp.context)
    self.assertIn(u"num_bookmarks", resp.context)
    self.assertIn(u"collection_url", resp.context)
    self.assertIn(u"collection_add_bookmarklet", resp.context)
    self.assertEqual(1,resp.context["user_bookmarks"].paginator.count)
    self.assertEqual([self.bkm_b],
             list(resp.context["user_bookmarks"]))
 
  def test_get_html_anonymous_returns_all(self):
    # request uA's collection
    resp = self.client.get(
      reverse("wom_user.views.user_collection",
          kwargs={"owner_name":"uA"}))
    self.assertEqual(200,resp.status_code)
    self.assertIn("collection.html",
            [t.name for t in resp.templates])
    self.assertIn(u"user_bookmarks", resp.context)
    self.assertIn(u"num_bookmarks", resp.context)
    self.assertIn(u"collection_url", resp.context)
    self.assertIn(u"collection_add_bookmarklet", resp.context)
    self.assertEqual(1,resp.context["user_bookmarks"].paginator.count)
    self.assertEqual([self.bkm],
             list(resp.context["user_bookmarks"]))


class UserCollectionAddTest(TestCase,UserBookmarkAddTestMixin):
  
  def setUp(self):
    UserBookmarkAddTestMixin.setUp(self)
  
  def add_request(self,username,optionsDict,expectedStatusCode=302):
    """
    Send the request as a GET with some url parameters.
    """
    url = reverse("wom_user.views.user_collection_add",
            kwargs={"owner_name":username})\
            +"?"+"&".join(\
      "%s=%s" % t for t in optionsDict.items())
    url = url.replace(" ","%20")
    resp = self.client.get(url)
    self.assertEqual(expectedStatusCode,resp.status_code)
    return resp


class UserBookmarkViewTest(TestCase):
  """Test the bookmark view."""
  
  def setUp(self):
    self.date = datetime.now(timezone.utc)
    self.reference = Reference.objects.create(
      url=u"http://bla",
      title=u"a bla",
      pub_date=self.date)
    self.source1 = Reference.objects.create(
      url=u"http://blaSrc1",
      title=u"a source",
      pub_date=self.date)
    self.source2 = Reference.objects.create(
      url=u"http://blaSrc2",
      title=u"a source2",
      pub_date=self.date)
    self.reference.sources.add(self.source1)
    self.reference.sources.add(self.source2)
    self.user = User.objects.create_user(username="uA",
                                         password="pA")
    self.user_profile = UserProfile.objects.create(owner=self.user)
    self.bkm = UserBookmark.objects.create(
      owner=self.user,
      reference=self.reference,
      saved_date=self.date,
      is_public=True)
    set_item_tag_names(self.user, self.reference, ["T1","T2"])
    self.other_user = User.objects.create_user(username="uB",
                                               password="pB")

  def change_request(self,username,reference_url,optionsDict,expectedStatusCode=200):
    """
    Send the request as a JSON loaded POST.
    """
    resp = self.client.post(reverse("wom_user.views.user_collection_item",
                                    kwargs={"owner_name":username,
                                            "reference_url": reference_url}),
                simplejson.dumps(optionsDict),
                content_type="application/json")
    self.assertEqual(expectedStatusCode,resp.status_code)
    return resp
    
  def test_get_html_user_bookmark(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    resp = self.client.get(reverse("wom_user.views.user_collection_item",
                                   kwargs={"owner_name":"uA",
                                           "reference_url":self.reference.url}))
    self.assertEqual(200,resp.status_code)
    self.assertIn("bookmark_edit.html",[t.name for t in resp.templates])
    self.assertIn("ref_form", resp.context)
    self.assertIn("bmk_form", resp.context)
    self.assertIn("ref_url", resp.context)
    self.assertEqual(self.reference.url, resp.context["ref_url"])
    self.assertIn("ref_title", resp.context)
    self.assertEqual(self.reference.title, resp.context["ref_title"])
    self.assertIn("ref_sources", resp.context)
    self.assertEqual([s for s in self.bkm.get_sources()],
                     [s for s in resp.context["ref_sources"]])
    self.assertIn("ref_tags", resp.context)
    self.assertEqual([n for n in self.bkm.get_tag_names()],
                     [n for n in resp.context["ref_tags"]])

  def test_get_html_other_user_bookmark_is_forbidden(self):
    self.assertTrue(self.client.login(username="uB",password="pB"))
    resp = self.client.get(reverse("wom_user.views.user_collection_item",
                                   kwargs={"owner_name":"uA",
                                           "reference_url":self.reference.url}))
    self.assertEqual(403,resp.status_code)
    
  def test_change_user_bookmark_title_updates_title_in_db(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    newTitle = self.reference.title + "MOUF"
    self.change_request("uA",self.reference.url,
                        {"ref-title": newTitle,
                         "ref-description": u"blah"}, 302)
    self.assertEqual(newTitle,
                     Reference.objects.get(url=self.reference.url).title)
    
  def test_change_user_bookmark_comment_updates_comment_in_db(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    newComment = self.bkm.comment + " NEW"
    self.change_request("uA",self.reference.url,
                        {"bmk-comment": newComment}, 302)
    self.assertEqual(newComment,
                     UserBookmark.objects.get(reference=self.reference).comment)

  def test_change_user_bookmark_privacy_updates_privacy_in_db(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    newPrivacy = not self.bkm.is_public
    self.change_request("uA",self.reference.url,
                        {"bmk-is_public": newPrivacy}, 302)
    self.assertEqual(newPrivacy,
                     UserBookmark.objects.get(reference=self.reference).is_public)


class ImportUserBookmarksFromNSListMixin:

  def setUpWithContent(self, content):
    # Create a single reference with its source, and a user with a
    # single bookmark on this reference. Create also another user to
    # check for user data isolation.
    date = datetime.now(timezone.utc)
    self.source = Reference.objects.create(
      url=u"http://mouf",
      title=u"mouf",
      pub_date=date)
    reference = Reference.objects.create(
      url=u"http://mouf/a",
      title=u"glop",
      pub_date=date,
      pin_count=1)
    reference.sources.add(self.source)
    reference.add_pin()
    self.user = User.objects.create_user(username="uA",
                                         password="pA")
    self.user_profile = UserProfile.objects.create(owner=self.user)
    self.user_profile.sources.add(self.source)
    self.bkm = UserBookmark.objects.create(
        owner=self.user,
        reference=reference,
        saved_date=date)
    self.other_user = User.objects.create_user(username="uB",
                                               password="pB")
    import_user_bookmarks_from_ns_list(self.user, content)
  
  def test_bookmarks_are_added(self):
    self.assertEqual(2,self.user.userbookmark_set.count())
    bmk_urls = [b.reference.url for b in self.user.userbookmark_set.all()]
    self.assertIn("http://www.example.com",bmk_urls)
    self.assertIn("http://mouf/a",bmk_urls)
    self.assertEqual("The example",
                     UserBookmark.objects\
                     .get(reference__url="http://www.example.com")\
                     .reference.title)
    self.assertEqual("glop",
                     UserBookmark.objects\
                     .get(reference__url="http://mouf/a")\
                     .reference.title)
                         
  def test_bookmarked_reference_pin_count_updated(self):
    self.assertEqual(2,self.user.userbookmark_set.count())
    for b in self.user.userbookmark_set.all():
      self.assertEqual(1,b.reference.pin_count,
                       "Wrong save count %s for %s" % (b.reference.pin_count,
                                                       b.reference))
    
  def test_check_bookmarks_not_added_to_other_user(self):
    self.assertEqual(0,self.other_user.userbookmark_set.count())
  
  def test_check_tags_correctly_added(self):
    # Check that tags were added too
    self.assertTrue(Tag.objects.filter(name="example").exists())
    self.assertTrue(Tag.objects.filter(name="html").exists())
    self.assertTrue(Tag.objects.filter(name="test").exists())
    
  def test_check_tags_correctly_associated_to_bmks(self):
    # Check that tags were correctly associated with the bookmarks
    ref_tags = get_item_tag_names(self.user,
                                  Reference\
                                  .objects.get(url="http://www.example.com"))
    self.assertEqual(set(["example","html"]),set(ref_tags))
    ref_tags = get_item_tag_names(self.user,
                                  Reference\
                                  .objects.get(url="http://mouf/a"))
    self.assertEqual(set(["test"]),set(ref_tags))

class ImportUserBookmarksFromNSListInTypicalCase(ImportUserBookmarksFromNSListMixin, TestCase):

  def setUp(self):
    nsbmk_txt = """\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<!-- This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
<DT><A HREF="http://www.example.com" ADD_DATE="1367951483" PRIVATE="1" TAGS="example,html">The example</A>
<DD>An example bookmark.
<DT><A HREF="http://mouf/a" ADD_DATE="1366828226" PRIVATE="0" TAGS="test">The mouf</A>
"""
    self.setUpWithContent(nsbmk_txt)

class ImportUserBookmarksFromNSListWithHtmlTagLowerCase(ImportUserBookmarksFromNSListMixin, TestCase):

  def setUp(self):
    nsbmk_txt = """\
<!doctype netscape-bookmark-file-1>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<!-- This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<title>Bookmarks</title>
<h1>Bookmarks</H1>
<dl><p>
<dt><a href="http://www.example.com" add_date="1367951483" private="1" tags="example,html">The example</a>
<dd>An example bookmark.
<dt><a href="http://mouf/a" add_date="1366828226" private="0" tags="test">The mouf</a>
"""
    self.setUpWithContent(nsbmk_txt)

class ImportUserBookmarksFromNSListAfterBrowserBeautification(ImportUserBookmarksFromNSListMixin, TestCase):

  def setUp(self):
    nsbmk_txt = """\
<!DOCTYPE netscape-bookmark-file-1>
<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<!-- This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<title>Bookmarks</title>
</head><body><h1>WaterOnMars pebbles collected by demo</h1>
<dl><p>

</p><dt><a href="http://www.example.com" add_date="1367951483" private="1" tags="example,html">The example</a>
</dt><dd>An example bookmark.

</dd><dt><a href="http://mouf/a" add_date="1366828226" private="0" tags="test">The mouf</a>
</dt></dl><p>
</p></body></html>
"""
    self.setUpWithContent(nsbmk_txt)
