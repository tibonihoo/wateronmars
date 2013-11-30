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


import datetime
from django.utils import timezone

from django.test import TestCase
from django.db import IntegrityError

from wom_pebbles.models import Reference
from wom_pebbles.models import URL_MAX_LENGTH
from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.tasks  import build_reference_title_from_url
from wom_pebbles.tasks  import truncate_reference_title
from wom_pebbles.tasks  import import_references_from_ns_bookmark_list


if URL_MAX_LENGTH>255:
  print "WARNING: the current max length for URLs may cause portability problems (see https://docs.djangoproject.com/en/1.4/ref/databases/#character-fields)"
    
class ReferenceModelTest(TestCase):

  def setUp(self):
    self.test_date = datetime.datetime.now(timezone.utc)
    
  def test_construction_defaults(self):
    """
    This tests just makes it possible to double check that a
    change in the default is voluntary.
    """
    r = Reference.objects.create(url="http://mouf",title="glop",
                                 pub_date=self.test_date)    
    self.assertEqual(r.url,"http://mouf")
    self.assertEqual(r.title,"glop")
    self.assertEqual(r.description,"")
    
  def test_construction_with_max_length_url(self):
    """
    Test that the max length constant guarantees that a string of
    the corresponding length will be accepted.
    """
    max_length_url = "u"*URL_MAX_LENGTH
    r = Reference.objects.create(url=max_length_url,
                                 title="glop",
                                 pub_date=self.test_date)
    # Check also that url wasn't truncated
    self.assertEqual(max_length_url,r.url)

  def test_construction_with_max_length_title(self):
    """
    Test that the max length constant guarantees that a string of
    the corresponding length will be accepted.
    """
    max_length_title = "u"*REFERENCE_TITLE_MAX_LENGTH
    s = Reference.objects.create(url="http://mouf",
                                 title=max_length_title,
                                 pub_date=self.test_date)
    # Check also that title wasn't truncated
    self.assertEqual(max_length_title,s.title)

  def test_unicity_of_urls(self):
    """
    Test the unicity guaranty on names.
    """
    s = Reference.objects.create(url="http://mouf",
                                 title="glop",
                                 pub_date=self.test_date)
    self.assertRaises(IntegrityError,
                      Reference.objects.create,
                      url=s.url,
                      title="paglop",
                      pub_date=self.test_date)


  def test_get_productions(self):
    date = datetime.datetime.now(timezone.utc)
    source = Reference.objects.create(
      url=u"http://mouf",
      title=u"mouf",
      pub_date=date)
    reference = Reference.objects.create(
      url=u"http://mouf/a",
      title=u"glop",
      pub_date=date)
    reference.sources.add(source)
    self.assertEqual(reference,source.productions.get())


class UtilityFunctionsTests(TestCase):

  def test_build_reference_title_from_url(self):
    ref_title = build_reference_title_from_url("http://mif/maf/mouf")
    self.assertEqual("mif/maf/mouf",ref_title)
    ref_title = build_reference_title_from_url("http://mif/maf/mouf.php")
    self.assertEqual("mif/maf/mouf.php",ref_title)
    ref_title = build_reference_title_from_url("http://glop.mif/maf/mouf.php")
    self.assertEqual("glop.mif/maf/mouf.php",ref_title)
    ref_title = build_reference_title_from_url("http://glop.mif/")
    self.assertEqual("glop.mif",ref_title)
    ref_title = build_reference_title_from_url("internal://glop.mif/maf/mouf.php")
    self.assertEqual("glop.mif/maf/mouf.php",ref_title)
    ref_title = build_reference_title_from_url("/glop.mif/maf/mouf.php")
    self.assertEqual("/glop.mif/maf/mouf.php",ref_title)
    ref_title = build_reference_title_from_url("http://")
    self.assertEqual("",ref_title)

  def test_truncate_reference_title(self):
    ref_title = "mouf"
    self.assertTrue(len(ref_title)<REFERENCE_TITLE_MAX_LENGTH)
    self.assertEqual(ref_title,truncate_reference_title(ref_title))
    ref_title = "m"*REFERENCE_TITLE_MAX_LENGTH
    self.assertEqual(ref_title,truncate_reference_title(ref_title))
    ref_title = "p" + "m"*REFERENCE_TITLE_MAX_LENGTH
    self.assertEqual("...",truncate_reference_title(ref_title)[-3:])


class ImportReferencesFromNSBookmarkListTaskTest(TestCase):

  def setUp(self):
    date = datetime.datetime.now(timezone.utc)
    self.source = Reference.objects.create(
      url=u"http://mouf",
      title=u"mouf",
      pub_date=date)
    self.reference = Reference.objects.create(
      url=u"http://mouf/a",
      title=u"glop",
      pub_date=date)
    self.reference.sources.add(self.source)
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
<DD>This is just a test
<DT><A HREF="http://%s" ADD_DATE="1366828226" PRIVATE="0" TAGS="test">Long</A>
<DD>A too long URL.
</DL><p>
""" % ("u"*(URL_MAX_LENGTH))
    self.bmk_and_metadata = import_references_from_ns_bookmark_list(nsbmk_txt)
    
  def test_references_are_added_with_correct_urls(self):
    references_in_db = list(Reference.objects.all())
    # 5: 3 bookmarks + 2 sources
    self.assertEqual(5,len(references_in_db))
    ref_urls = [r.url for r in references_in_db]
    self.assertIn("http://www.example.com",ref_urls)
    self.assertIn("http://mouf/a",ref_urls)
    max_length_urls = [u for u in ref_urls if len(u)==URL_MAX_LENGTH]
    self.assertEqual(1,len(max_length_urls))
    self.assertTrue(max_length_urls[0].startswith("http://uuu"))
    
  def test_references_are_added_with_correct_title(self):
    ref_title = Reference.objects.get(url="http://www.example.com").title
    self.assertEqual("The example",ref_title)
    ref_title = Reference.objects.get(url="http://mouf/a").title
    self.assertEqual("glop",ref_title)
    ref_title = Reference.objects.get(url__contains="uuu").title 
    self.assertEqual("Long",ref_title)
    # Additional check here to see if we managed to use the
    # description field to 'save' url info from oblivion.
    self.assertIn("http://uuu",
                  Reference.objects.get(url__contains="uuu").description)
    
  def test_check_metadata_correctly_associated_to_refs(self):
    self.assertEqual(3,len(self.bmk_and_metadata))
    urls = [r.url for r in self.bmk_and_metadata]
    urls.sort(key=lambda u:len(u))
    self.assertIn("http://www.example.com",urls)
    self.assertIn("http://mouf/a",urls)
    self.assertTrue(urls[-1].startswith("http://uuu"))
    meta = self.bmk_and_metadata[
      Reference.objects.get(url="http://www.example.com")]
    self.assertEqual(set(["example","html"]),meta.tags)
    self.assertEqual("An example bookmark.",meta.note)
    self.assertFalse(meta.is_public)
    meta = self.bmk_and_metadata[
      Reference.objects.get(url="http://mouf/a")]
    self.assertEqual(set(["test"]),meta.tags)
    self.assertEqual("This is just a test",meta.note)
    self.assertTrue(meta.is_public)
    meta = self.bmk_and_metadata[
      Reference.objects.get(url=urls[-1])]
    self.assertEqual(set(["test"]),meta.tags)
    self.assertEqual("A too long URL.",meta.note)
    self.assertTrue(meta.is_public)

