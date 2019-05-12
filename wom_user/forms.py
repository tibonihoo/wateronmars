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

from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from wateronmars import settings

from wom_pebbles.models import URL_MAX_LENGTH
from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import Reference
from wom_pebbles.tasks import build_reference_title_from_url
from wom_pebbles.tasks import build_source_url_from_reference_url
from wom_pebbles.tasks import sanitize_url

from wom_river.models import WebFeed

from wom_user.models import UserProfile
from wom_user.models import UserBookmark
from wom_user.models import ReferenceUserStatus

from wom_river.utils import feedfinder
feedfinder.setUserAgent(settings.USER_AGENT)


class OPMLFileUploadForm(forms.Form):
  """From used to upload an OPML file."""
  opml_file  = forms.FileField("OPML file")

class NSBookmarkFileUploadForm(forms.Form):
  """From used to upload an Netscape-style bookmarks file."""
  bookmarks_file  = forms.FileField("Bookmarks file")


class UserProfileCreationForm(UserCreationForm):
  """Customized form to require an email and create a profile at the same time as creating a user."""

  email = forms.EmailField(required=True)

  def save(self, commit=True):
    """
    Warning: the User instance will be saved whether commit is True or False.
    Returns a UserProfile instance (not saved if commit==False).
    """
    user = super(UserProfileCreationForm, self).save(commit=False)
    user.email = self.cleaned_data["email"]
    user.save()
    profile = UserProfile()
    profile.owner = user
    if commit:
      profile.save()
    return profile

class UserBookmarkAdditionForm(forms.Form):
  """Collect all necessary data to add a new bookmark to a user's collection."""

  url = forms.CharField(max_length=URL_MAX_LENGTH, required=True,
                        widget=forms.TextInput(attrs={"class":"form-control"}))
  title = forms.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH, required=False,
                          widget=forms.TextInput(attrs={"class":"form-control"}))
  comment = forms.CharField(required=False,
                            widget=forms.Textarea(
                              attrs={"class":"form-control","rows":"5"}))
  pub_date = forms.DateTimeField(required=False,widget=forms.DateTimeInput(attrs={"class":"form-control"}))
  source_title = forms.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH,
                                 required=False,
                                 widget=forms.TextInput(
                                   attrs={"class":"form-control"}))
  source_url = forms.CharField(max_length=URL_MAX_LENGTH,required=False,
                               widget=forms.TextInput(
                                 attrs={"class":"form-control"}))

  def __init__(self,user, *args, **kwargs):
    forms.Form.__init__(self,*args,**kwargs)
    self.user = user

  def save(self):
    """Warning: the bookmark will be saved as well as the related objects
    (no commit options).
    Returns the bookmark.
    """
    url,_ = sanitize_url(self.cleaned_data["url"])
    title = self.cleaned_data["title"] \
            or build_reference_title_from_url(url)
    comment = self.cleaned_data["comment"]
    pub_date = self.cleaned_data["pub_date"] \
               or datetime.now(timezone.utc)
    src_url,_ = sanitize_url(self.cleaned_data["source_url"] \
                             or build_source_url_from_reference_url(url))
    src_title = self.cleaned_data["source_title"] \
               or build_reference_title_from_url(src_url)
    # Find or create a matching reference
    try:
      bookmarked_ref = Reference.objects.get(url=url)
      # Arbitrarily chose one of the possible sources
      src_query = bookmarked_ref.sources
      if src_query.count() > 1:
        ref_src = src_query.all()[0]
      else:
        ref_src = src_query.get()
    except ObjectDoesNotExist:
      try:
        ref_src = Reference.objects.get(url=src_url)
      except ObjectDoesNotExist:
        ref_src = Reference(url=src_url,title=src_title,pub_date=pub_date)
        ref_src.save()
      if src_url == url:
        bookmarked_ref = ref_src
      else:
        bookmarked_ref = Reference(url=url,
                                   title=title,
                                   pub_date=pub_date)
        bookmarked_ref.save()
        bookmarked_ref.sources.add(ref_src)
        bookmarked_ref.save()
    with transaction.commit_on_success():
      try:
        bmk = UserBookmark.objects.get(owner=self.user,reference=bookmarked_ref)
      except ObjectDoesNotExist:
        bmk = UserBookmark(owner=self.user,reference=bookmarked_ref,
                           saved_date=datetime.now(timezone.utc))
        bookmarked_ref.save_count += 1
        bmk.save()
        bookmarked_ref.save()
      # allow the user-specific comment to be changed and also prefix
      # it with the user specified title if it differs from the
      # existing reference title.
      if comment:
        new_comment = comment
      else:
        new_comment = bmk.comment
      if self.cleaned_data["title"] and title!=bookmarked_ref.title \
         and not new_comment.startswith(title):
        new_comment = "%s: %s" % (title,new_comment)
      if new_comment!=bmk.comment:
        bmk.comment = new_comment
        bmk.save()
    with transaction.commit_on_success():
      if ref_src not in self.user.userprofile.sources.all():
        self.user.userprofile.sources.add(ref_src)
        self.user.userprofile.save()
    with transaction.commit_on_success():
      for rust in ReferenceUserStatus\
        .objects.filter(owner=self.user,
                        reference=bookmarked_ref).all():
        rust.has_been_saved = True
        rust.save()
    return bmk


class UserSourceAdditionForm(forms.Form):
  """Collect all necessary data to subscribe to a new source."""

  url = forms.CharField(max_length=URL_MAX_LENGTH, required=True,
                        widget=forms.TextInput(
                          attrs={"class":"form-control"}))
  title = forms.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH,
                         required=False,
                         widget=forms.TextInput(
                           attrs={"class":"form-control"}))
  feed_url = forms.CharField(max_length=URL_MAX_LENGTH, required=True,
                             widget=forms.TextInput(
                               attrs={"class":"form-control"}))

  def __init__(self,user, *args, **kwargs):
    forms.Form.__init__(self,*args,**kwargs)
    self.user = user

  def clean(self):
    """Used to set the right feed_url if it hasn't been given."""
    cleaned_data = super(UserSourceAdditionForm, self).clean()
    url = cleaned_data.get("url")
    if not url:
      raise forms.ValidationError("The source URL is required.")
    feed_url = cleaned_data.get("feed_url")
    if feed_url and feedfinder.isFeed(feed_url.encode("utf-8"),checkRobotAllowed=False):
      return cleaned_data
    if feedfinder.isFeed(url.encode("utf-8"),checkRobotAllowed=False):
      cleaned_data["feed_url"] = url
      return cleaned_data
    # the feed is not here or invalid: let's see if we can find some
    # valid feed urls by ourselves.
    feed_error_msg = u"Please give the URL of an existing valid feed."
    candidates = set(unicode(f) for f in feedfinder.feeds(url.encode("utf-8")))
    if not candidates:
      self._errors["feed_url"] = self.error_class([feed_error_msg])
      raise forms.ValidationError(u"Impossible to find feeds at the given URL or even to discover one related to the source's URL")
    # A little sorting will help making a good guess when several
    # candidates are available.
    # For Wordpress blogs at least there is usually several feeds
    # one of which is the comment feed and is "probably not" the one
    # the user wants to subscribe when giving only the url to the
    # said blog.
    second_candidates = set(f for f in candidates if u"comment" in f)
    candidates = list(candidates - second_candidates) + list(second_candidates)
    if feed_url:
      # The user has given a URL, and we cannot exchange it without
      # asking a confirmation
      # TODO: try to see if one of the candidates is close enough that
      # the first URL could be a typo
      self._errors["feed_url"] = self.error_class([feed_error_msg])
      raise forms.ValidationError(u"There is no valid field at the given URL (maybe you meant one of %s)" % candidates)
    # try to guess the right feed for the URL
    best_guess_url = unicode(candidates[0])
    if len(candidates)>1:
      # too much sources, we should ask the user to select one of
      # these. TODO: do this with a better UX that raw display of URLs
      self._errors["feed_url"] = self.error_class([feed_error_msg])
      # get a mutable copy of the querydict and change it to add a
      # default value for the feed_url
      data = self.data.copy()
      data["feed_url"] = best_guess_url
      self.data = data
      raise forms.ValidationError(u"There are several feeds related to the source at '%s', please select one of them (candidate URLs: %s)" % (url,candidates))
    # only one candidate and no feed proposed by the user, let's
    # select it arbitrarily
    cleaned_data["feed_url"] = best_guess_url
    return cleaned_data


  def save(self):
    """Warning: the source will be saved as well as the related objects
    (no commit options).
    Returns the source.
    """
    form_url,_ = sanitize_url(self.cleaned_data["url"])
    form_title = self.cleaned_data["title"]
    form_feed_url,_ = sanitize_url(self.cleaned_data["feed_url"])
    if self.user.userprofile.web_feeds.filter(source__url=form_url).exists():
      # nothing to do
      return
    # try a bigger look-up anyway
    same_sources = WebFeed.objects.filter(source__url=form_url).all()
    # url are unique for sources
    if same_sources:
      new_feed = same_sources[0]
    else:
      if form_title:
        source_title = form_title
      else:
        source_title = build_reference_title_from_url(form_url)
      try:
        source_ref = Reference.objects.get(url=form_url)
      except ObjectDoesNotExist:
        source_ref = Reference(url=form_url,title=source_title,
                               pub_date=datetime.now(timezone.utc))
        source_ref.save()
      new_feed = WebFeed(source=source_ref)
      # assume that either form_feed_url or form_url have been
      # validated as a valid feed url
      new_feed.xmlURL = form_feed_url or form_url
      new_feed.last_update_check = datetime.utcfromtimestamp(0)\
                                           .replace(tzinfo=timezone.utc)
      new_feed.save()
    with transaction.commit_on_success():
      source_ref.save_count += 1
      source_ref.save()
      self.user.userprofile.sources.add(source_ref)
      self.user.userprofile.public_sources.add(source_ref)
      self.user.userprofile.web_feeds.add(new_feed)
      self.user.userprofile.save()
    return new_feed


class ReferenceEditForm(ModelForm):
  """Designed to modify a reference."""

  class Meta:
    model = Reference
    fields = ("title", "description", "pub_date")


class UserBookmarkEditForm(ModelForm):
  """Designed to modify a bookmark."""

  class Meta:
    model = UserBookmark
    fields = ("comment", "is_public")


class WebFeedOptInOutForm(forms.Form):
  """Designed to allow unsubscribing to a given feed."""
  follow = forms.BooleanField(required=False)

  def __init__(self,user, feed, *args, **kwargs):
    forms.Form.__init__(self,*args,**kwargs)
    self.user = user
    self.feed = feed

  def save(self):
    """Note: this save can have only one effect: removing a feed from the user's feed list."""
    if self.cleaned_data["follow"]:
      self.user.userprofile.web_feeds.add(self.feed)
      self.user.userprofile.save()
    else:
      self.user.userprofile.web_feeds.remove(self.feed)
      self.user.userprofile.save()


from wom_tributary.models import TwitterTimeline
from wom_tributary.models import TwitterUserInfo
from wom_tributary.models import GeneratedFeed

class UserTwitterSourceAdditionForm(forms.Form):
  """Collect all necessary data to subscribe to a new twitter source."""

  title = forms.CharField(
    max_length=GeneratedFeed.TITLE_MAX_LENGTH,
    required=True,
    widget=forms.TextInput(attrs={"class":"form-control"}))

  username = forms.CharField(
    max_length=TwitterUserInfo.USERNAME_MAX_LENGTH,
    required=True,
    widget=forms.TextInput(attrs={"class":"form-control"}))

  def __init__(self, user, *args, **kwargs):
    forms.Form.__init__(self,*args,**kwargs)
    self.user = user

  def save(self):
    """Warning: the source will be saved as well as the related objects
    (no commit options).
    Returns the source.
    """
    form_title = self.cleaned_data['title']
    form_username = self.cleaned_data['username']
    source_url = TwitterTimeline.SOURCE_URL
    source_name = "Twitter"
    source_pub_date = datetime.now(timezone.utc)
    provider = GeneratedFeed.TWITTER
    # Make sure that this specific user profile has a
    # corresponding user info to be sure it doesn't share
    # credentials with another's user profile just
    # by writting down this other's user's twitter username !
    same_twitter_info = self.user.userprofile.twitter_info
    same_twitter = TwitterTimeline.objects.filter(
      username=form_username).all()
    # url are unique for sources
    if same_twitter_info and same_twitter:
      return same_twitter[0].generated_feed.source
    if not same_twitter_info:
      new_twitter_user = TwitterUserInfo(username=form_username)
      new_twitter_user.save()
      self.user.userprofile.twitter_info = new_twitter_user
      self.user.userprofile.save()
      same_twitter_info = new_twitter_user
    any_twitter_sources = Reference.objects.filter(
      url = source_url,
      ).all()
    with transaction.commit_on_success():
      if any_twitter_sources:
        twitter_source = any_twitter_sources[0]
      else:
        twitter_source = Reference(
          url=source_url, title=source_name,
          pub_date=source_pub_date)
      twitter_source.save_count += 1
      twitter_source.save()
    with transaction.commit_on_success():
      new_feed = GeneratedFeed(
        provider=provider,
        source=twitter_source, title=form_title)
      new_feed.last_update_check = (
        datetime
        .utcfromtimestamp(0)
        .replace(tzinfo=timezone.utc)
        )
      new_feed.save()
    with transaction.commit_on_success():
      new_twitter = TwitterTimeline(
        username=form_username,
        generated_feed=new_feed,
        twitter_user_access_info = same_twitter_info)
      new_twitter.save()
      if twitter_source not in self.user.userprofile.sources.all():
        self.user.userprofile.sources.add(twitter_source)
      self.user.userprofile.generated_feeds.add(new_feed)
      self.user.userprofile.save()
    return twitter_source
