from urlparse import urlparse

import datetime
from django.utils import timezone

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from wateronmars import settings

from wom_pebbles.models import URL_MAX_LENGTH
from wom_pebbles.models import SOURCE_NAME_MAX_LENGTH
from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import Reference
from wom_pebbles.models import Source

from wom_river.models import FeedSource
from wom_river.models import ReferenceUserStatus

from wom_user.models import UserProfile
from wom_user.models import UserBookmark

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
    profile.user = user
    if commit:
      profile.save()
    return profile

class UserBookmarkAdditionForm(forms.Form):
  """Collect all necessary data to add a new bookmark to a user's collection."""
  # TODO: distinguish reference description from user-specific note !
  url = forms.CharField(max_length=URL_MAX_LENGTH, required=True, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  title = forms.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH, required=True, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  description = forms.CharField(required=False,widget=forms.Textarea(attrs={"class":"input-xxlarge"}))
  pub_date = forms.DateField(required=False)
  source_name = forms.CharField(max_length=SOURCE_NAME_MAX_LENGTH,required=False, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  source_url = forms.CharField(max_length=URL_MAX_LENGTH,required=False, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  
  def __init__(self,user, *args, **kwargs):
    forms.Form.__init__(self,*args,**kwargs)
    self.user = user
  
  def save(self):
    """Warning: the bookmark will be saved as well as the related objects
    (no commit options).
    Returns the bookmark.
    """
    form_url = self.cleaned_data["url"]
    form_title = self.cleaned_data["title"]
    form_description = self.cleaned_data["description"]
    form_pub_date = self.cleaned_data["pub_date"]
    form_source_url = self.cleaned_data["source_url"]
    form_source_name = self.cleaned_data["source_name"]
    if self.user.userbookmark_set.filter(reference__url=form_url).exists():
      b = self.user.userbookmark_set.filter(reference__url=form_url)[0]
      if form_title and b.reference.title != form_title:
        b.reference.title = form_title
      if form_description and b.reference.description != form_description:
        b.reference.description = form_description
      if form_source_url:
        if b.reference.source.url == form_source_url:
          if form_source_name and b.reference.source.name != form_source_name:
            b.reference.source.name = form_source_name
          b.reference.source.save()
        else:
          same_sources = Source.objects.filter(url=form_source_url).all()
          # impose the new source
          if same_sources:
            # url are unique for sources
            b.reference.source = same_sources[0]
          else:
            bookmark_source = Source()
            bookmark_source.url = form_source_url
            # find the source name or generate a reasonable one
            if form_source_name:
              bookmark_source_name = form_source_name
            else:
              url_cpt = urlparse(form_source_url)
              bookmark_source_name = url_cpt.hostname or ""
              if url_cpt.path.split("/") and url_cpt.path != "/":
                bookmark_source_name +=  url_cpt.path
            bookmark_source.name = bookmark_source_name
            bookmark_source.save()
            b.reference.source = bookmark_source
      b.reference.save()
    else:
      # lookup a matching Reference
      same_url_refs = Reference.objects.filter(url=form_url)
      if form_source_url:
        bookmark_source_url = form_source_url
      else:
        url_cpt = urlparse(form_url)
        if url_cpt.scheme:
          prefix = url_cpt.scheme+"://"
        else:
          prefix = ""
        bookmark_source_url = (prefix+url_cpt.netloc) or form_url
      same_sources = self.user.userprofile.sources.filter(url=bookmark_source_url).all()
      if same_sources:
        user_has_same_source = True
      else:
        user_has_same_source = False
        # try a bigger look-up anyway
        same_sources = Source.objects.filter(url=bookmark_source_url).all()
      # url are unique for sources
      if same_sources:
        bookmark_source = same_sources[0]
        refs_with_same_source = same_url_refs.filter(source=bookmark_source)
      else:
        bookmark_source = None
        refs_with_same_source = None
      if refs_with_same_source:
        # take the first that comes...
        bookmarked_ref = refs_with_same_source[0]
      elif same_url_refs.exists():
        # take the first that comes...
        bookmarked_ref = same_url_refs[0]
      else:
        if bookmark_source is None:
          # find the source name or generate a reasonable one
          if form_source_name:
            bookmark_source_name = form_source_name
          else:
            url_cpt = urlparse(bookmark_source_url)
            bookmark_source_name = url_cpt.hostname or ""
            if url_cpt.path.split("/") and url_cpt.path != "/":
              bookmark_source_name +=  url_cpt.path
          bookmark_source = Source()
          bookmark_source.url = bookmark_source_url
          bookmark_source.name = bookmark_source_name
          bookmark_source.save()
        bookmarked_ref = Reference()
        bookmarked_ref.source = bookmark_source
        bookmarked_ref.url = form_url
        bookmarked_ref.title = form_title
        # for lack of a better source of info
        bookmarked_ref.pub_date = form_pub_date or datetime.datetime.now(timezone.utc)-datetime.timedelta(weeks=12)
        bookmarked_ref.description = form_description
        bookmarked_ref.save()
        bookmarked_ref.tags = bookmark_source.tags.all()
        bookmarked_ref.save()
      with transaction.commit_on_success():
        b = UserBookmark()
        b.owner = self.user
        b.saved_date = datetime.datetime.now(timezone.utc)-datetime.timedelta(weeks=12)
        b.reference = bookmarked_ref
        bookmarked_ref.save_count += 1
        b.save()
        bookmarked_ref.save()
      with transaction.commit_on_success():
        if not user_has_same_source:
          self.user.userprofile.sources.add(bookmarked_ref.source)
          self.user.userprofile.save()
        b.tags = bookmarked_ref.tags.all()
        b.save()
    with transaction.commit_on_success():
      for rust in ReferenceUserStatus.objects.filter(user=self.user,ref__url=form_url).all():
        rust.has_been_saved = True
        rust.save()
    return b


class UserSourceAdditionForm(forms.Form):
  """Collect all necessary data to subscribe to a new source."""

  url = forms.CharField(max_length=URL_MAX_LENGTH, required=True, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  name = forms.CharField(max_length=SOURCE_NAME_MAX_LENGTH, required=False, widget=forms.TextInput(attrs={"class":"input-large"}))
  feed_url = forms.CharField(max_length=URL_MAX_LENGTH, required=True, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  
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
    form_url = self.cleaned_data["url"]
    form_name = self.cleaned_data["name"]
    form_feed_url = self.cleaned_data["feed_url"]
    if self.user.userprofile.feed_sources.filter(url=form_url).exists():
      # nothing to do
      return
    # try a bigger look-up anyway
    same_sources = FeedSource.objects.filter(url=form_url).all()
    # url are unique for sources
    if same_sources:
      new_source = same_sources[0]
    else:
      if form_name:
        source_name = form_name
      else:
        url_cpt = urlparse(form_url)
        source_name = url_cpt.hostname or ""
        if url_cpt.path.split("/") and url_cpt.path != "/":
          source_name +=  url_cpt.path
      new_source = FeedSource()
      new_source.url = form_url
      new_source.name = source_name
      # assume that either form_feed_url or form_url have been
      # validated as a valid feed url
      new_source.xmlURL = form_feed_url or form_url
      new_source.last_update = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=timezone.utc)
      new_source.is_public = True
      new_source.save()      
    if not self.user.userprofile.sources.filter(url=form_url).exists():
      self.user.userprofile.sources.add(new_source)
    self.user.userprofile.feed_sources.add(new_source)
    self.user.save()
    return new_source

def CreateUserSourceRemovalForm(user,*args, **kwargs):
      
  class UserSourceRemovalForm(forms.Form):
    """Gather a selection of syndication sources from which the user wants to un-subsribe."""   
    sources_to_remove = forms.ModelMultipleChoiceField(\
      user.userprofile.feed_sources,
      widget=forms.SelectMultiple(attrs={"class":"input-xxlarge","size":"13"}))
    
    def __init__(self):
      forms.Form.__init__(self,*args,**kwargs)
      self.user = user
   
    def save(self,commit=True):
      """Unsubscribe the user from the selected sources and returns
      the list of un-subscribed sources.

      If commit is set to False, the changes to the UserProfile object
      are not commited.
      """
      sources_to_remove = self.cleaned_data["sources_to_remove"] 
      for feed_source in sources_to_remove:
        self.user.userprofile.feed_sources.remove(feed_source)
      if commit:
        self.user.userprofile.save()
      return sources_to_remove
  
  return UserSourceRemovalForm()
