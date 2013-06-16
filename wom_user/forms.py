from urlparse import urlparse

import datetime
from django.utils import timezone

from django import forms
from django.contrib.auth.forms import UserCreationForm

from django.db import transaction

from wom_pebbles.models import URL_MAX_LENGTH
from wom_pebbles.models import SOURCE_NAME_MAX_LENGTH
from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import Reference
from wom_pebbles.models import Source

from wom_river.models import ReferenceUserStatus

from wom_user.models import UserProfile
from wom_user.models import UserBookmark


class OPMLFileUploadForm(forms.Form):
  """From used to upload an OPML file."""
  opml_file  = forms.FileField("OPML file")

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
  
  url = forms.URLField(max_length=URL_MAX_LENGTH, required=True, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  title = forms.CharField(max_length=REFERENCE_TITLE_MAX_LENGTH, required=True, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  description = forms.CharField(required=False,widget=forms.Textarea(attrs={"class":"input-xxlarge"}))
  pub_date = forms.DateField(required=False)
  source_name = forms.CharField(max_length=SOURCE_NAME_MAX_LENGTH,required=False, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  source_url = forms.URLField(max_length=URL_MAX_LENGTH,required=False, widget=forms.TextInput(attrs={"class":"input-xxlarge"}))
  
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
    if not self.user.userbookmark_set.filter(reference__url=form_url).exists():
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
      for rust in ReferenceUserStatus.objects.filter(ref__url=form_url).all():
        rust.has_been_saved = True
        rust.save()
    return b
  
