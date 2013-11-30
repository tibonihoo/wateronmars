#!/usr/bin/env python
# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

"""Read bookmarks saved in a "Netscape bookmark" format
as exported by Microsoft Internet Explorer or Delicious.com (and
initially of course by Netscape).

Assumptions:
- The file is a Netscape bookmark file.
  See a doc at http://msdn.microsoft.com/en-us/library/aa753582%28v=VS.85%29.aspx
- There is only one record by line.
- If a decription/comment/note is attached to the bookmark, it is on
  a line prefixed with <DD> (and nothing else but the note should be
  on the same line).

License: 2-clause BSD

Copyright (c) 2013, Thibauld Nion
All rights reserved.
 
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
 
1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
 
2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED ²AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import urllib2
import sys
import os
import re


# The following prefix is not enough to identify a bookmark line (may
# be a folder with '<H3 FOLDED' for instance), so that the line has to
# be checked against the RE_BOOKMARK_URL too.
BOOKMARK_LINE_PREFIX = "<DT>"
BOOKMARK_NOTE_PREFIX = "<DD>"
DOCTYPE_LINE = "<!DOCTYPE NETSCAPE-Bookmark-file-1>"
# Regular expression to extract info about the bookmark
RE_BOOKMARK_URL = re.compile('HREF="(?P<url>[^"]+)"')
RE_BOOKMARK_COMPONENTS = {
  "posix_timestamp" : re.compile('ADD_DATE="(?P<posix_timestamp>\d+)"'),
  "tags"   : re.compile('TAGS="(?P<tags>[\w,]+)"'),
  "private": re.compile('PRIVATE="(?P<private>\d)"'),
  "title"  : re.compile('<A[^>]*>(?P<title>[^<]*)<'),
  }


def is_netscape_bookmarks_file(candidateFile):
  """Return True if the file looks like a valid Netscape bookmark file."""
  correct_doctype_found = False
  for line in candidateFile:
    line = line.lstrip()
    if line.startswith(DOCTYPE_LINE):
      correct_doctype_found = True
    if not line and not correct_doctype_found:
      return False
  if correct_doctype_found:
    return True
  return False


def parse_netscape_bookmarks(bookmarkHTMFile):
  """Extract bookmarks and return them in a list of dictionaries formatted in the following way:
  [ {"url":"http://...", "title":"the title", "private":"0"/"1", "tags":"tag1,tag2,...", "posix_timestamp"="<unix time>", "note":"description"}]
  Raise a ValueError if the format is wrong.
  """
  bookmark_list = []
  last_line_is_bmk = False
  correct_doctype_found = False
  for line in bookmarkHTMFile.splitlines():
    line = line.lstrip()
    if line.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"):
      correct_doctype_found = True
      continue
    if line.rstrip() and not correct_doctype_found:
      raise ValueError("Couldn't find a correct DOCTYPE in the bookmark file (wrong format?)")
    if line.startswith(BOOKMARK_LINE_PREFIX):
      # we will successively apply the various regexes until we get
      # all the bookmark's info
      m = RE_BOOKMARK_URL.search(line)
      if not m:
        # No url => skip this line
        continue
      bmk = {"url":m.group("url")}
      for cpnt_name,cpnt_re in RE_BOOKMARK_COMPONENTS.items():
        m = cpnt_re.search(line)
        if m: bmk[cpnt_name] = m.group(cpnt_name)
      bookmark_list.append(bmk)
      last_line_is_bmk = True
    elif last_line_is_bmk and line.startswith(BOOKMARK_NOTE_PREFIX):
      last_line_is_bmk = False
      bookmark_list[-1]["note"] = line[4:].strip()
    else:
      last_line_is_bmk = False
  return bookmark_list

def expand_url(url):
  opener = urllib2.build_opener()
  opener.addheaders = [('User-agent', 'netscape_bookmarks.py')]
  initial_url = url
  new_url = None
  while new_url != url:
    if new_url is not None:
      url = new_url
    try:
      res = opener.open(url)
      if str(res.getcode())[0] in (5,4):
        # something bad happened, reutrn the url as is
        print "Keeping url %s as is because of an HTTP error %s" % (initial_url,res.getcode())
        return initial_url
    except urllib2.HTTPError,e:
      print "Keeping url %s as is because of an HTTP error %s (%s)" % (initial_url,e.code, e.reason)
      return initial_url
    except urllib2.URLError,e:
      print "Keeping url %s as is because of an URL error %s" % (initial_url,e.reason)
      return initial_url
    except Exception,e:
      print "Keeping url %s as is because of an unexpected error %s" % (initial_url,e)
      return initial_url
    new_url = res.geturl()
  return url
  
def expand_short_urls(bookmarkHTMFile,outputFile):
  """Filter the bookmark file in such a way that the shortened url are expanded.""" 
  correct_doctype_found = False
  outputLines = []
  for line in bookmarkHTMFile:
    line = line.lstrip()
    if line.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"):
      correct_doctype_found = True
    if not line and not correct_doctype_found:
      raise ValueError("Couldn't find a correct DOCTYPE in the bookmark file (wrong format?)")
    if line.startswith(BOOKMARK_LINE_PREFIX):
      # we will successively apply the various regexes until we get
      # all the bookmark's info
      m = RE_BOOKMARK_URL.search(line)
      if m:
        bmk_url = m.group("url")
        expanded_url = expand_url(bmk_url)
        # if bmk_url != expanded_url:
        #   print "Expanding %s to %s" % (bmk_url, expanded_url)
        line = line.replace(bmk_url,expanded_url)
        # specific line for Delicous export that have several "None"
        # titled links when the link has itself been extracted from twitter.
        if "from twitter" in line:
          line = line.replace(">None</A>",">%s</A>" % expanded_url)
    outputLines.append(line)
    if len(outputLines)==1000:
      print "flush %s" % outputLines[0]
      outputFile.write("\n".join(outputLines))
      del outputLines[:]
  outputFile.write("\n".join(outputLines))

  
  
if __name__ == '__main__':
  USAGE = """\
USAGE: netscape_bookmarks.py PRINT bookmarkfilepath.html
    or netscape_bookmarks.py EXPAND  bookmarkfilepath.html
In the second case a new file is created called bookmarkfilepath_expanded.html
"""
  if len(sys.argv) !=3:
    print USAGE
    sys.exit(2)
  if sys.argv[1]=="PRINT":
    bookmarks = parse_netscape_bookmarks(open(sys.argv[2], 'r+'))
    print "Found %d bookmarks" % len(bookmarks)
    for b in bookmarks:
      print "  - %s: %s" % (b.get("title","<no title>"), b["url"])
  elif sys.argv[1]=="EXPAND":
    input_file_path = os.path.abspath(sys.argv[2])
    input_path,input_ext = os.path.splitext(input_file_path)
    new_file_path = input_path+"_expanded"+input_ext
    expand_short_urls(open(input_file_path,"r+"),open(new_file_path,"w"))
    print "Bookmarks file with expanded short urls is at %s" % new_file_path
