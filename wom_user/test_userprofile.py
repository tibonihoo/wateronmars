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

from django.test import TestCase

from wom_user.models import UserProfile

from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

class UserProfileModelTest(TestCase):

  def setUp(self):
    self.user = User.objects.create(username="name")
    
  def test_accessible_info(self):
    """
    Just to be sure what info we can access (not a "unit" test per
    se but useful anyway to make sure the model given enough
    information and list the info we rely on)
    """
    p = UserProfile.objects.create(owner=self.user)
    self.assertEqual(p.owner,self.user)
    self.assertEqual(0,len(p.sources.all()))
    self.assertEqual(0,len(p.web_feeds.all()))
    # just to be sure it is still provided by django
    self.assertNotEqual(p.owner.date_joined,None)


class UserProfileViewTest(TestCase):

  def setUp(self):
    self.user_a = User.objects.create_user(username="A",
                          password="pA")
    
  def test_get_html_user_profile(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="A",password="pA"))
    resp = self.client.get(reverse("user_profile"))
    self.assertEqual(200,resp.status_code)
    self.assertIn("profile.html",[t.name for t in resp.templates])
    self.assertIn("username", resp.context)
    self.assertEqual("A", resp.context["username"])
    self.assertIn("opml_form", resp.context)
    self.assertIn("nsbmk_form", resp.context)
    self.assertIn("collection_add_bookmarklet", resp.context)
    self.assertIn("source_add_bookmarklet", resp.context)

  def test_get_html_anonymous_profile(self):
    resp = self.client.get(reverse("user_profile"))
    self.assertEqual(302,resp.status_code)
