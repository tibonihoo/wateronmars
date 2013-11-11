# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

import datetime
from django.utils import timezone
from django.utils import simplejson

from django.http import HttpResponse
from django.core.urlresolvers import reverse

from django.test import TestCase

from django.test.client import RequestFactory

from wom_pebbles.models import Reference
from wom_pebbles.models import Source
from wom_river.models import FeedSource

from wom_user.models import UserProfile
from wom_user.models import UserBookmark

from wom_user.views import check_and_set_owner
from wom_user.views import loggedin_and_owner_required
from wom_user.tasks import import_user_feedsources_from_opml
from wom_user.tasks import import_user_bookmarks_from_ns_list

from wom_classification.models import Tag
from wom_classification.models import get_item_tag_names

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

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
    self.assertEqual(0,len(p.sources.all()))
    self.assertEqual(0,len(p.feed_sources.all()))
    # just to be sure it is still provided by django
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


class CheckAndSetOwnerDecoratorTest(TestCase):

  def setUp(self):
    self.test_user_a = User.objects.create(username="A")
    self.test_user_b = User.objects.create(username="B")
    self.request_factory = RequestFactory()
    def pass_through(request,owner_name):
      resp = HttpResponse()
      resp.request = request
      return resp
    self.pass_through_func = pass_through
    
  def test_call_with_user_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = self.test_user_a
    res = check_and_set_owner(self.pass_through_func)(req,"A")
    self.assertEqual(200,res.status_code)
    self.assertTrue(hasattr(res.request,"owner_user"))
    self.assertEqual("A",res.request.owner_user.username)
    
  def test_call_with_non_owner_user(self):
    req = self.request_factory.get("/mouf")
    req.user = self.test_user_b
    res = check_and_set_owner(self.pass_through_func)(req,"A")
    self.assertEqual(200,res.status_code)
    self.assertTrue(hasattr(res.request,"owner_user"))
    self.assertEqual("A",res.request.owner_user.username)
    
  def test_call_for_invalid_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = self.test_user_b
    res = check_and_set_owner(self.pass_through_func)(req,"C")
    self.assertEqual(404,res.status_code)


class LoggedInAndOwnerRequiredDecoratorTest(TestCase):

  def setUp(self):
    self.test_user_a = User.objects.create(username="A")
    self.test_user_b = User.objects.create(username="B")
    self.request_factory = RequestFactory()
    def pass_through(request,owner_name):
      resp = HttpResponse()
      resp.request = request
      return resp
    self.pass_through_func = pass_through
    
  def test_call_with_user_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = self.test_user_a
    res = loggedin_and_owner_required(self.pass_through_func)(req,
                                  "A")
    self.assertEqual(200,res.status_code)
    self.assertTrue(hasattr(res.request,"owner_user"))
    self.assertEqual("A",res.request.owner_user.username)
    
  def test_call_with_non_owner_user(self):
    req = self.request_factory.get("/mouf")
    req.user = self.test_user_b
    res = loggedin_and_owner_required(self.pass_through_func)(req,"A")
    self.assertEqual(403,res.status_code)
    
  def test_call_for_invalid_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = AnonymousUser()
    res = loggedin_and_owner_required(self.pass_through_func)(req,"A")
    self.assertEqual(302,res.status_code)
    
class UserProfileViewTest(TestCase):

  def setUp(self):
    self.test_user_a = User.objects.create_user(username="A",
                          password="pA")
    
  def test_get_html_user_profile(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="A",password="pA"))
    resp = self.client.get(reverse("wom_user.views.user_profile"))
    self.assertEqual(200,resp.status_code)
    self.assertIn("wom_user/profile.html",[t.name for t in resp.templates])
    self.assertIn("username", resp.context)
    self.assertEqual("A", resp.context["username"])
    self.assertIn("opml_form", resp.context)
    self.assertIn("nsbmk_form", resp.context)
    self.assertIn("collection_add_bookmarklet", resp.context)
    self.assertIn("source_add_bookmarklet", resp.context)

  def test_get_html_anonymous_profile(self):
    resp = self.client.get(reverse("wom_user.views.user_profile"))
    self.assertEqual(302,resp.status_code)

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
    test_date = datetime.datetime.now(timezone.utc)
    self.test_source = Source.objects.create(
      url=u"http://mouf",
      name=u"mouf")
    test_reference = Reference.objects.create(
      url=u"http://mouf/a",
      title=u"glop",
      pub_date=test_date,
      source=self.test_source)
    test_reference_private = Reference.objects.create(
      url=u"http://mouf/b",
      title=u"nop",
      pub_date=test_date,
      source=self.test_source)
    test_reference_b = Reference.objects.create(
      url=u"http://mouf/b",
      title=u"paglop",
      pub_date=test_date,
      source=self.test_source)
    self.test_user = User.objects.create_user(username="uA",
                                              password="pA")
    p = UserProfile.objects.create(user=self.test_user)
    p.sources.add(self.test_source)
    self.test_bkm = UserBookmark.objects.create(
      owner=self.test_user,
      reference=test_reference,
      saved_date=test_date,
      is_public=True)
    self.test_bkm_private = UserBookmark.objects.create(
      owner=self.test_user,
      reference=test_reference_private,
      saved_date=test_date)
    self.test_other_user = User.objects.create_user(username="uB",
                                                    password="pB")
    self.test_bkm_b = UserBookmark.objects.create(
      owner=self.test_other_user,
      reference=test_reference_b,
      saved_date=test_date,
      is_public=True)
  
  def test_post_json_new_item_is_added(self):
    """
    Posting a bookmark will add it to the user's collection.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["num_bookmarks"])
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": u"http://new/mouf",
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": u"http://glop",
                  "source_name": u"new name",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(3,resp.context["num_bookmarks"])
    items = resp.context["user_bookmarks"]
    self.assertIn(u"http://new/mouf",[b.reference.url for b in items])
    self.assertIn(u"mouf",[b.comment for b in items \
                           if b.reference.url==u"http://new/mouf"])

  def test_post_json_new_item_is_added_without_source(self):
    """
    Posting a bookmark without providing a source will
    add the bookmark correctly anyway.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["num_bookmarks"])
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
    self.assertEqual(3,resp.context["num_bookmarks"])
    items = resp.context["user_bookmarks"]
    self.assertIn(u"http://new/mouf",[b.reference.url for b in items])
    self.assertIn(u"http://new", [b.reference.source.url for b in items],
            "Unexpexted guess for the source URL !")
    self.assertIn(u"mouf",[b.comment for b in items \
                           if b.reference.url==u"http://new/mouf"])

  def test_post_json_new_item_is_added_with_existing_source_url(self):
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
    self.assertEqual(2,resp.context["num_bookmarks"])
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": u"http://new/mouf",
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": self.test_source.url,
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(3,resp.context["num_bookmarks"])
    items = resp.context["user_bookmarks"]
    self.assertIn(u"http://new/mouf",[b.reference.url for b in items])
    self.assertIn(u"mouf",[b.comment for b in items \
                           if b.reference.url==u"http://new/mouf"])
    self.assertEqual(self.test_source,
             Reference.objects.get(url=u"http://new/mouf").source)
    self.assertEqual(1,Source.objects.filter(url=self.test_source.url).count())

  def test_post_json_new_item_is_added_with_existing_url(self):
    """
    Posting a bookmark with a url for which a bookmark already
    exists will update the bookmark's title and description.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["num_bookmarks"])
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": self.test_bkm.reference.url,
                  "title": u"new title",
                  "comment": u"mouf",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["num_bookmarks"])
    self.assertIn(self.test_bkm.reference.url,
            [b.reference.url for b  in resp.context["user_bookmarks"]])
    self.assertEqual(1,
             Reference.objects\
               .filter(url=self.test_bkm.reference.url).count())
    r = Reference.objects.get(url=self.test_bkm.reference.url)
    self.assertEqual(self.test_source.url,r.source.url)
    # The ref info hasn't changed
    self.assertEqual(u"glop",r.title)
    self.assertEqual(u"",r.description)
    self.assertEqual(u"new title: mouf",
                     UserBookmark.objects.get(reference=r).comment)
    
  def test_post_json_new_item_is_added_with_existing_url_other_source(self):
    """
    Posting a bookmark with a url for which a bookmark already
    exists will update the bookmark's title, description and source.
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",password="pA"))
    # check presence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["num_bookmarks"])
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": self.test_bkm.reference.url,
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": u"http://barf",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["num_bookmarks"])
    self.assertIn(self.test_bkm.reference.url,
            [b.reference.url for b  in resp.context["user_bookmarks"]])
    self.assertEqual(1,
             Reference.objects\
               .filter(url=self.test_bkm.reference.url).count())
    r = Reference.objects.get(url=self.test_bkm.reference.url)
    # The source has not changed
    self.assertEqual(u"http://mouf",r.source.url)
    # The ref info has not changed
    self.assertEqual(u"glop",r.title)
    self.assertEqual(u"",r.description)
    self.assertEqual(u"new title: mouf",
                     UserBookmark.objects.get(reference=r).comment)
    
  def test_post_json_new_item_is_added_with_existing_url_same_source(self):
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
    self.assertEqual(2,resp.context["num_bookmarks"])
    # mark the first reference as read.
    resp = self.add_request("uA",
                { "url": self.test_bkm.reference.url,
                  "title": u"new title",
                  "comment": u"mouf",
                  "source_url": self.test_source.url,
                  "source_name": u"new name",
                  })
    # resp_dic = simplejson.loads(resp.content)
    # self.assertEqual("success",resp_dic["status"])
    # check absence of r1 reference
    resp = self.client.get(reverse("wom_user.views.user_collection",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(2,resp.context["num_bookmarks"])
    self.assertIn(self.test_bkm.reference.url,
            [b.reference.url for b  in resp.context["user_bookmarks"]])
    self.assertEqual(1,
             Reference.objects\
               .filter(url=self.test_bkm.reference.url).count())
    r = Reference.objects.get(url=self.test_bkm.reference.url)
    self.assertEqual(self.test_source.url,r.source.url)
    # The source name has not changed
    self.assertEqual(u"mouf",r.source.name)
    # The ref info has not changed
    self.assertEqual(u"glop",r.title)
    self.assertEqual(u"",r.description)
    self.assertEqual(u"new title: mouf",
                     UserBookmark.objects.get(reference=r).comment)
  
  def test_post_json_new_item_to_other_user_fails(self):
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
               "source_name": u"new name",
               },
             expectedStatusCode=403)
    

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
    self.assertIn("wom_user/collection.html_dt",
            [t.name for t in resp.templates])
    self.assertIn(u"user_bookmarks", resp.context)
    self.assertIn(u"num_bookmarks", resp.context)
    self.assertIn(u"collection_url", resp.context)
    self.assertIn(u"collection_add_bookmarklet", resp.context)
    self.assertEqual(2,resp.context["num_bookmarks"])
    self.assertEqual(2,len(resp.context["user_bookmarks"]))
    self.assertEqual(set([self.test_bkm,self.test_bkm_private]),
                     set(resp.context["user_bookmarks"]))
    # test additional attribute
    self.assertNotIn(False,[hasattr(b,"tag_names") \
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
    self.assertIn("wom_user/collection.html_dt",
            [t.name for t in resp.templates])
    self.assertIn(u"user_bookmarks", resp.context)
    self.assertIn(u"num_bookmarks", resp.context)
    self.assertIn(u"collection_url", resp.context)
    self.assertIn(u"collection_add_bookmarklet", resp.context)
    self.assertEqual(1,resp.context["num_bookmarks"])
    self.assertEqual([self.test_bkm_b],
             list(resp.context["user_bookmarks"]))
 
  def test_get_html_anonymous_returns_all(self):
    # request uA's collection
    resp = self.client.get(
      reverse("wom_user.views.user_collection",
          kwargs={"owner_name":"uA"}))
    self.assertEqual(200,resp.status_code)
    self.assertIn("wom_user/collection.html_dt",
            [t.name for t in resp.templates])
    self.assertIn(u"user_bookmarks", resp.context)
    self.assertIn(u"num_bookmarks", resp.context)
    self.assertIn(u"collection_url", resp.context)
    self.assertIn(u"collection_add_bookmarklet", resp.context)
    self.assertEqual(1,resp.context["num_bookmarks"])
    self.assertEqual([self.test_bkm],
             list(resp.context["user_bookmarks"]))


class UserCollectionViewAddTest(TestCase,UserBookmarkAddTestMixin):
  
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

  
class UserSourceAddTestMixin:
  """Mixin implementing the common tests for the Form and the REST API
  of source addition.
  """
  
  def add_request(self,url,optionsDict):
    """
    Returns the response that can be received from the input url.
    """
    raise NotImplementedError("This method should be reimplemented")

  def del_request(self,url,optionsDict):
    """
    Returns the response that can be received from the input url.
    """
    raise NotImplementedError("This method should be reimplemented")
  
  def setUp(self):
    self.test_date = datetime.datetime.now(timezone.utc)
    self.test_source = Source.objects.create(
      url=u"http://mouf",
      name=u"a mouf")
    self.test_user = User.objects.create_user(username="uA",
                          password="pA")
    self.test_feed_source = FeedSource.objects.create(
      xmlURL="http://barf/bla.xml",
      last_update_check=self.test_date,
      url="http://barf",name="a barf")
    self.test_user_profile = UserProfile.objects.create(user=self.test_user)
    self.test_user_profile.sources.add(self.test_source)
    self.test_user_profile.sources.add(self.test_feed_source)
    self.test_user_profile.feed_sources.add(self.test_feed_source)
    self.test_other_user = User.objects.create_user(username="uB",
                            password="pB")
    self.test_other_profile = UserProfile.objects.create(\
      user=self.test_other_user)
    self.test_source_b = Source.objects.create(
      url=u"http://glop",
      name=u"a glop")
    self.test_other_profile.sources.add(self.test_source_b)

  def test_add_new_feed_source_to_owner(self):
    """
    WARNING: dependent on an internet access !
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(2,self.test_user_profile.sources.count())
    self.assertEqual(1,self.test_user_profile.feed_sources.count())
    self.add_request("uA",
             {"url": u"http://cyber.law.harvard.edu/rss/examples/rss2sample.xml",
              "feed_url": u"http://cyber.law.harvard.edu/rss/examples/rss2sample.xml",
              "name": u"a new"})
    self.assertEqual(3,self.test_user_profile.sources.count())
    self.assertEqual(2,self.test_user_profile.feed_sources.count())
    self.assertIn("http://cyber.law.harvard.edu/rss/examples/rss2sample.xml",
            [s.url for s in self.test_user_profile.sources.all()])
    
  def test_add_new_feed_source_to_other_user_fails(self):
    """
    WARNING: dependent on an internet access !
    """
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(2,self.test_user_profile.sources.count())
    self.assertEqual(1,self.test_user_profile.feed_sources.count())
    self.add_request("uB",
             {"url": u"http://cyber.law.harvard.edu/rss/examples/rss2sample.xml",
              "feed_url": u"http://cyber.law.harvard.edu/rss/examples/rss2sample.xml",
              "name": u"a new"},
             expectedStatusCode=403)
    
  # def test_remove_source(self):
  #   # login as uA and make sure it succeeds
  #   self.assertTrue(self.client.login(username="uA",
  #                     password="pA"))
  #   self.assertEqual(2,self.test_user_profile.sources.count())
  #   self.assertEqual(1,self.test_user_profile.feed_sources.count())
  #   self.remove_request("uA",
  #             {"url": u"http://barf",
  #              "feed_url": u"http://barf/bla.xml",
  #              "name": u"a new"})
  #   self.assertEqual(1,self.test_user_profile.sources.count())
  #   self.assertEqual(0,self.test_user_profile.feed_sources.count())
  #   self.assertNotIn("http://barf",
  #            [s.url for s in self.test_user_profile.sources.all()])
  
class UserSourceViewTest(TestCase,UserSourceAddTestMixin):

  def setUp(self):
    UserSourceAddTestMixin.setUp(self)
  
  def add_request(self,username,optionsDict,expectedStatusCode=302):
    """
    Send the request as a JSON loaded POST (a redirect is expected
    in case of success).
    """
    resp = self.client.post(reverse("wom_river.views.user_river_sources",
                    kwargs={"owner_name":username}),
                simplejson.dumps(optionsDict),
                content_type="application/json")
    self.assertEqual(expectedStatusCode,resp.status_code)
    return resp
  
  def test_get_sources_for_owner(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    resp = self.client.get(reverse("wom_river.views.user_river_sources",
                     kwargs={"owner_name":"uA"}))
    self.assertEqual(200, resp.status_code)
    self.assertIn("visitor_name",resp.context)
    self.assertIn("source_add_bookmarklet",resp.context)
    self.assertIn("owner_name",resp.context)
    self.assertIn("syndicated_sources",resp.context)
    self.assertIn("referenced_sources",resp.context)
    self.assertEqual("uA",resp.context["owner_name"])
    self.assertEqual(1,len(resp.context["syndicated_sources"]))
    self.assertEqual("http://barf",resp.context["syndicated_sources"][0].url)
    self.assertEqual(1,len(resp.context["referenced_sources"]))
    self.assertEqual("http://mouf",resp.context["referenced_sources"][0].url)


class ImportUserBookmarksFromNSList(TestCase):

  def setUp(self):
    # Create a single reference with its source, and a user with a
    # single bookmark on this reference. Create also another user to
    # check for user data isolation.
    date = datetime.datetime.now(timezone.utc)
    self.source = Source.objects.create(
        url=u"http://mouf",
        name=u"mouf")
    reference = Reference.objects.create(
        url=u"http://mouf/a",
        title=u"glop",
        pub_date=date,
      source=self.source)
    self.user = User.objects.create_user(username="uA",
                                         password="pA")
    self.user_profile = UserProfile.objects.create(user=self.user)
    self.user_profile.sources.add(self.source)
    self.bkm = UserBookmark.objects.create(
        owner=self.user,
        reference=reference,
        saved_date=date)
    self.other_user = User.objects.create_user(username="uB",
                                               password="pB")
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
    import_user_bookmarks_from_ns_list(self.user,nsbmk_txt)
  
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


class ImportUserFeedSourceFromOPMLTaskTest(TestCase):

  def setUp(self):
    # Create 2 users but only create sources for one of them.
    self.user = User.objects.create_user(username="uA",password="pA")
    self.user_profile = UserProfile.objects.create(user=self.user)
    self.other_user = User.objects.create_user(username="uB",password="pB")
    self.other_user_profile = UserProfile.objects.create(user=self.other_user)
    date = datetime.datetime.now(timezone.utc)
    fs1 = FeedSource.objects.create(xmlURL="http://mouf/rss.xml",
                                    last_update_check=date,
                                    url="http://mouf",name="f1")
    fs3 = FeedSource.objects.create(xmlURL="http://greuh/rss.xml",
                                    last_update_check=date,
                                    url="http://greuh",name="f3")
    self.user_profile.feed_sources.add(fs1)
    self.user_profile.feed_sources.add(fs3)
    self.user_profile.sources.add(fs1)
    self.user_profile.sources.add(fs3)
    # also add plain sources
    s1 = Source.objects.create(url="http://s1",name="s1")
    s3 = Source.objects.create(url="http://s3",name="s3")
    self.user_profile.sources.add(s1)
    self.user_profile.sources.add(s3)
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
    import_user_feedsources_from_opml(self.user,opml_txt)
    
  def test_check_sources_correctly_added(self):
    self.assertEqual(7,self.user_profile.sources.count())
    self.assertEqual(5,self.user_profile.feed_sources.count())
    feed_urls = [s.xmlURL for s in self.user_profile.feed_sources.all()]
    self.assertIn("http://stallman.org/rss/rss.xml",feed_urls)
    self.assertIn("http://www.scripting.com/rss.xml",feed_urls)
    self.assertIn("http://www.openculture.com/feed",feed_urls)
    
  def test_check_sources_not_added_to_other_user(self):
    self.assertEqual(0,self.other_user_profile.sources.count())
    self.assertEqual(0,self.other_user_profile.feed_sources.count())
    
  def test_check_tags_correctly_added(self):
    # Check that tags were added too
    self.assertTrue(Tag.objects.filter(name="News").exists())
    self.assertTrue(Tag.objects.filter(name="Culture").exists())
    
  def test_check_tags_correctly_associated_to_sources(self):
    # Check that tags were correctly associated with the sources
    src_tags = get_item_tag_names(self.user,
      FeedSource.objects.get(url="http://scripting.com/"))
    self.assertEqual(["News"],src_tags)
    src_tags = get_item_tag_names(self.user,
      FeedSource.objects.get(url="http://stallman.org/archives/polnotes.html"))
    self.assertEqual(["News"],src_tags)
    src_tags = get_item_tag_names(self.user,
      FeedSource.objects.get(url="http://mouf"))
    self.assertEqual(["News"],src_tags)
    src_tags = get_item_tag_names(self.user,
      FeedSource.objects.get(url="http://www.openculture.com"))
    self.assertEqual(["Culture"],src_tags)

