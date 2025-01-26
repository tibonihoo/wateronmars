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


import datetime
from django.utils import timezone

from django.test import TestCase
from django.db import IntegrityError

from wom_pebbles.models import (
    Reference,
    URL_MAX_LENGTH,
    REFERENCE_TITLE_MAX_LENGTH,
    build_url_from_safe_code,
    build_safe_code_from_url,
    )

from wom_pebbles.tasks import (
    build_reference_title_from_url,
    truncate_reference_title,
    sanitize_url,
    import_references_from_ns_bookmark_list,
    )

from wom_pebbles.templatetags.html_sanitizers  import defang_html


if URL_MAX_LENGTH>255:
  print("WARNING: the current max length for URLs may cause portability problems (see https://docs.djangoproject.com/en/1.4/ref/databases/#character-fields)")

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
      url="http://mouf",
      title="mouf",
      pub_date=date)
    reference = Reference.objects.create(
      url="http://mouf/a",
      title="glop",
      pub_date=date)
    reference.sources.add(source)
    self.assertEqual(reference,source.productions.get())

  def test_url_safe_code(self):
    url = "https://mouf/mif/maf/?+"
    r = Reference.objects.create(
      url=url,title="glop",
      pub_date=self.test_date)
    url_safe_code = r.url_safe_code
    url_decoded = build_url_from_safe_code(url_safe_code)
    self.assertEqual(url, url_decoded)

  def test_build_url_from_safe_code_round_trips(self):
     url = "https://mouf/mif/maf/?+"
     code = build_safe_code_from_url(url)
     url_decoded = build_url_from_safe_code(code)
     self.assertEqual(url, url_decoded)


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
    ref_title = "p " + "m"*(REFERENCE_TITLE_MAX_LENGTH-1)
    self.assertEqual("p...",truncate_reference_title(ref_title))

  def test_sanitize_url_on_short_ascii_url(self):
    short_url = "http://mouf"
    self.assertTrue(len(short_url)<URL_MAX_LENGTH)
    self.assertEqual((short_url,False),sanitize_url(short_url))

  def test_sanitize_url_on_long_ascii_url(self):
    long_url = "http://" + ("u"*URL_MAX_LENGTH)
    res_long_url,did_truncate = sanitize_url(long_url)
    self.assertTrue(did_truncate)
    self.assertGreaterEqual(URL_MAX_LENGTH,len(res_long_url))

  def test_sanitize_url_on_long_ascii_url_with_campain_args(self):
    query_start = "/?"
    campain_string = "utm_source=rss&utm_medium=rss&utm_campaign=on-peut"
    filler_size = URL_MAX_LENGTH-7-len(campain_string)-len(query_start)+1
    long_url_campain = "http://" + ("u"*filler_size) + query_start + campain_string
    res_long_url,did_truncate = sanitize_url(long_url_campain)
    self.assertTrue(did_truncate)
    self.assertGreaterEqual(URL_MAX_LENGTH,len(res_long_url))
    self.assertEqual(long_url_campain[:-len(campain_string)],res_long_url)

  def test_sanitize_url_with_non_ascii_characters(self):
    short_url = "http://méhœñ۳予"
    self.assertTrue(len(short_url)<URL_MAX_LENGTH)
    escaped_url= "http://m%C3%A9h%C5%93%C3%B1%DB%B3%E4%BA%88"
    self.assertEqual((escaped_url,False),sanitize_url(short_url))

  def test_sanitize_url_with_long_after_quote_url(self):
    short_url = "http://é"
    short_url += ("u"*(URL_MAX_LENGTH-len(short_url)-1))
    self.assertTrue(len(short_url)<URL_MAX_LENGTH)
    truncated_url, did_truncate = sanitize_url(short_url)
    self.assertEqual(True,did_truncate)
    self.assertGreaterEqual(URL_MAX_LENGTH,len(truncated_url))

  def test_sanitize_url_with_spaces(self):
    short_url = "http://m m"
    self.assertTrue(len(short_url)<URL_MAX_LENGTH)
    escaped_url= "http://m%20m"
    self.assertEqual((escaped_url,False),sanitize_url(short_url))

  def test_sanitize_url_with_long_after_space_quote_url(self):
    short_url = "http://m m"
    short_url += ("u"*(URL_MAX_LENGTH-len(short_url)-1))
    self.assertTrue(len(short_url)<URL_MAX_LENGTH)
    truncated_url, did_truncate = sanitize_url(short_url)
    self.assertEqual(True,did_truncate)
    self.assertGreaterEqual(URL_MAX_LENGTH,len(truncated_url))


class ImportReferencesFromNSBookmarkListTaskTest(TestCase):

  def setUp(self):
    date = datetime.datetime.now(timezone.utc)
    self.source = Reference.objects.create(
      url="http://mouf",
      title="mouf",
      pub_date=date)
    self.reference = Reference.objects.create(
      url="http://mouf/a",
      title="glop",
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


class HTMLSanitizersTemplateTagsTest(TestCase):

  def test_defang_html_on_correct_html(self):
    html = """\
<div class="mouf"><p><span><img/>Hello</span><b>World!</b><script>...
    </script></p></div>"""
    safer_html = "<p><img>Hello<b>World!</b></p>"
    output = defang_html(html)
    self.assertEqual(safer_html,output)

  def test_defang_html_on_snippet_missing_span_close(self):
    html = """\
<div class="mouf"><p><span><img/>Hello <b>World!</b><script>...
    </script></p></div>"""
    safer_html = "<p><img>Hello <b>World!</b></p>"
    output = defang_html(html)
    self.assertEqual(safer_html,output)

  def test_defang_html_on_snippet_missing_p_close(self):
    html = """\
<div class="mouf"><p><span><img/>Hello <b>World!</b><script>...
    </script></div>"""
    safer_html = "<p><img>Hello <b>World!</b></p>"
    output = defang_html(html)
    self.assertEqual(safer_html,output)

  def test_defang_html_on_snippet_missing_b_close(self):
    html = """\
<div class="mouf"><p><span><img/>Hello <b>World!<script>...
    </script></p></div>"""
    safer_html = "<p><img>Hello <b>World!</b></p>"
    output = defang_html(html)
    self.assertEqual(safer_html,output)
