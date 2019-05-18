# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2019 Thibauld Nion
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

import sys
import re
from collections import defaultdict

MAX_CONTENT_SIZE_CHARS = 70
HASHTAG_REGEX = re.compile("(^|\s)#([\w\-\.]+)(\W|$)", re.UNICODE)
SUBJECT_REGEX = re.compile("(^\s*)([^:]{1,20})(:\s+\S+)", re.UNICODE)
NO_TAG = "<NO_TAG>"

from dateutil.parser import parse as parse_date


class Tweet:

  def __init__(self, link, content_summary, author, date, tags):
    self.link = link
    self.content_summary = content_summary
    self.author = author
    self.date = date
    self.tags = tags
    self.is_taken = False

  def __repr__(self):
    return " ".join([self.link, self.date])

  @staticmethod
  def from_activity_item(item):
    link = item[u"url"].encode("utf-8")
    details = item[u"object"]
    date = parse_date(details[u"published"])
    author_info = details[u"author"]
    author = (author_info.get(u"displayName") or author_info["username"]).encode("utf-8")
    content = details.get(u"content") or link # already encoded it seems
    matches = HASHTAG_REGEX.findall(content)
    if not matches:
      matches = SUBJECT_REGEX.findall(content)
    tags = [encode_and_fix_format(m[1]).strip() for m in matches if len(m)>1]
    content_summary = encode_and_fix_format(
        build_content_excerpt(content))
    return Tweet(link, content_summary, author, date, tags)


def build_content_excerpt(content_unicode):
  excerpt = content_unicode[:MAX_CONTENT_SIZE_CHARS]
  if len(excerpt) < len(content_unicode):
      excerpt += "(...)"
  return excerpt

def encode_and_fix_format(content_unicode):
  content_encoded = content_unicode.encode("utf-8")
  if sys.version_info.major == 2:
    s = str(content_encoded)
    if s.startswith("b'"):
      return s[2:-1]
  else:
    return content_encoded

def build_tweet_index_by_tag(data, keep_only_after_datetime):
  reverse_index = defaultdict(list)
  num_discarded = 0
  all_tweets = [Tweet.from_activity_item(item) for item in data]
  for tweet in sorted(all_tweets, key=lambda t: t.date):
    if tweet.date < keep_only_after_datetime:
      num_discarded += 1
      continue
    for tag in tweet.tags:
      reverse_index[tag].append(tweet)
    if not tweet.tags:
      reverse_index[NO_TAG].append(tweet)
  return reverse_index

def group_tweet_by_best_tag(reverse_index):
  tag_occurence_count = [(len(tweets), tag) for tag, tweets in reverse_index.items()]
  tweet_groups = {}
  for _, tag in sorted(tag_occurence_count, reverse=True):
    group = []
    for tweet in reverse_index[tag]:
      if not tweet.is_taken:
        group.append(tweet)
        tweet.is_taken=True
    tweet_groups[tag] = group
  return tweet_groups

def group_tweets_by_author(tweets):
  reverse_index = defaultdict(list)
  for item in tweets:
    reverse_index[item.author].append(item)
  return reverse_index


def build_reverse_index_cloud(reverse_index):
  freqs = list(sorted(len(t) for t in reverse_index.values()))
  num_reqs = len(freqs)
  num_quantiles = 10
  quantile_length = int(num_reqs/float(num_quantiles))
  threshold_index = min(num_reqs-1, (num_quantiles-1)*quantile_length)
  max_quantile = freqs[threshold_index]
  html_entries = []
  for entry, tweets in reverse_index.items():
    if entry == NO_TAG:
      continue
    current_freq = len(tweets)
    if quantile_length != 0 and current_freq > max_quantile:
      html_entries.append("<strong>{}</strong>".format(entry))
    else:
      html_entries.append("<small>{}</small>".format(entry))
  return html_entries


def get_items_sorted_by_dec_size_and_inc_key(reverse_index):
  return sorted(reverse_index.items(),
                  key=lambda item: (-len(item[1]), item[0]))


def generate_basic_html_summary(
    activities,
    keep_only_after_datetime):
  ridx = build_tweet_index_by_tag(
    activities,
    keep_only_after_datetime)
  groups = group_tweet_by_best_tag(ridx)
  singular_topics_tweets = []
  doc_lines = []
  html_tag_cloud = build_reverse_index_cloud(ridx)
  doc_lines.append("<p>")
  doc_lines.append("#{}".format(" #".join(html_tag_cloud)))
  doc_lines.append("</p>")
  all_tweets = []
  for tweets in groups.values():
    all_tweets.extend(tweets)
  all_tweets_by_author = group_tweets_by_author(all_tweets)
  html_author_cloud = build_reverse_index_cloud(all_tweets_by_author)
  doc_lines.append("<p>")
  doc_lines.append("@{}".format(" @".join(html_author_cloud)))
  doc_lines.append("</p>")
  doc_lines.append("<dl>")
  for tag, tweets in get_items_sorted_by_dec_size_and_inc_key(groups):
    if not tweets:
      continue
    if tag == NO_TAG or len(tweets)==1:
      singular_topics_tweets.extend(tweets)
      continue
    doc_lines.append("<dt>#{}</dt><dd>".format(tag))
    doc_lines.append("<ul>")
    for t in tweets:
      doc_lines.append("<li><em>@{}:</em> {} <a href='{}'>&#128279;</a></li>".format(t.author, t.content_summary, t.link))
    doc_lines.append("</ul></dd>")
  doc_lines.append("</dl>")
  if not singular_topics_tweets:
    return "\n".join(doc_lines)
  # Format remaining tweets, grouped by author
  doc_lines.append("<dl>")
  by_author = group_tweets_by_author(singular_topics_tweets)
  for author, tweets in get_items_sorted_by_dec_size_and_inc_key(by_author):
    doc_lines.append("<dt>@{}</dt><dd>".format(author))
    doc_lines.append("<ul>")
    for t in tweets:
      doc_lines.append("<li>{} <a href='{}'>&#128279;</a></li>".format(t.content_summary, t.link))
    doc_lines.append("</ul></dd>")
  doc_lines.append("</dl>")
  return "\n".join(doc_lines)
