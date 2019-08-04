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

from django.http import HttpResponse

from django.test import TestCase

from django.test.client import RequestFactory

from wom_user.views import check_and_set_owner
from wom_user.views import loggedin_and_owner_required

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

class CheckAndSetOwnerDecoratorTest(TestCase):

  def setUp(self):
    self.user_a = User.objects.create(username="A")
    self.user_b = User.objects.create(username="B")
    self.request_factory = RequestFactory()
    def pass_through(request,owner_name):
      resp = HttpResponse()
      resp.request = request
      return resp
    self.pass_through_func = pass_through
    
  def test_call_with_user_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = self.user_a
    res = check_and_set_owner(self.pass_through_func)(req,"A")
    self.assertEqual(200,res.status_code)
    self.assertTrue(hasattr(res.request,"owner_user"))
    self.assertEqual("A",res.request.owner_user.username)
    
  def test_call_with_non_owner_user(self):
    req = self.request_factory.get("/mouf")
    req.user = self.user_b
    res = check_and_set_owner(self.pass_through_func)(req,"A")
    self.assertEqual(200,res.status_code)
    self.assertTrue(hasattr(res.request,"owner_user"))
    self.assertEqual("A",res.request.owner_user.username)
    
  def test_call_for_invalid_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = self.user_b
    res = check_and_set_owner(self.pass_through_func)(req,"C")
    self.assertEqual(404,res.status_code)


class LoggedInAndOwnerRequiredDecoratorTest(TestCase):

  def setUp(self):
    self.user_a = User.objects.create(username="A")
    self.user_b = User.objects.create(username="B")
    self.request_factory = RequestFactory()
    def pass_through(request,owner_name):
      resp = HttpResponse()
      resp.request = request
      return resp
    self.pass_through_func = pass_through
    
  def test_call_with_user_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = self.user_a
    res = loggedin_and_owner_required(self.pass_through_func)(req,
                                  "A")
    self.assertEqual(200,res.status_code)
    self.assertTrue(hasattr(res.request,"owner_user"))
    self.assertEqual("A",res.request.owner_user.username)
    
  def test_call_with_non_owner_user(self):
    req = self.request_factory.get("/mouf")
    req.user = self.user_b
    res = loggedin_and_owner_required(self.pass_through_func)(req,"A")
    self.assertEqual(403,res.status_code)
    
  def test_call_for_invalid_owner(self):
    req = self.request_factory.get("/mouf")
    req.user = AnonymousUser()
    res = loggedin_and_owner_required(self.pass_through_func)(req,"A")
    self.assertEqual(302,res.status_code)
