# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2013-2019 Thibauld Nion
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
from django.utils.http import urlunquote_plus

from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wom_pebbles.models import Reference
from wom_classification.models import get_item_tag_names
from wom_classification.models import get_user_tags
from wom_pebbles.tasks import delete_old_references
from wom_river.tasks import collect_news_from_feeds

from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import QueryDict

from django.shortcuts import render_to_response
from django.utils import simplejson
from django.forms.util import ErrorList
from django.db import transaction

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout

from wom_river.models import WebFeed

from wom_tributary.models import GeneratedFeed

from wom_user.models import UserBookmark
from wom_user.models import ReferenceUserStatus

from wom_user.forms import OPMLFileUploadForm
from wom_user.forms import NSBookmarkFileUploadForm
from wom_user.forms import UserProfileCreationForm
from wom_user.forms import UserBookmarkAdditionForm
from wom_user.forms import UserSourceAdditionForm
from wom_user.forms import UserTwitterSourceAdditionForm
from wom_user.forms import ReferenceEditForm
from wom_user.forms import UserBookmarkEditForm
from wom_user.forms import WebFeedOptInOutForm


from wom_user.tasks import import_user_feedsources_from_opml
from wom_user.tasks import import_user_bookmarks_from_ns_list
from wom_user.tasks import check_user_unread_feed_items

from wom_user.settings import NEWS_TIME_THRESHOLD
from wom_user.settings import MAX_ITEMS_PER_PAGE
from wom_user.settings import HUMANS_TEAM
from wom_user.settings import HUMANS_THANKS



def check_and_set_owner(func):
  """
  Decorator that applies to functions expecting the "owner" name as a
  second argument.
  
  It will check if a user exists with this name and if so add to the
  request instance a member variable called owner_user pointing to the
  User instance corresponding to the owner.

  If the owner doesn't exists, the visitor is redirected to 404.
  """
  
  def _check_and_set_owner(request, owner_name, *args, **kwargs):
     try:
       owner_user = User.objects.get(username=owner_name)
     except User.DoesNotExist:
       return HttpResponseNotFound()
     else:
       request.owner_user = owner_user
       return func(request, owner_name, *args, **kwargs)
  return _check_and_set_owner


def loggedin_and_owner_required(func):
  """
  Decorator that applies to functions expecting the "owner" name as
  a second argument.

  It will check that the visitor is also considered as the owner of
  the resource it is accessing.

  Note: automatically calls login_required and check_and_set_owner decorators.
  """
  # TODO when not logged in send a 401 authentication requested and
  # implement corresponding template (at least send a 401 for non-GET
  # requests !)
  @login_required(login_url=settings.LOGIN_URL)
  @check_and_set_owner
  def _loggedin_and_owner_required(request, owner_name, *args, **kwargs):
    if request.user != request.owner_user:
      return HttpResponseForbidden()
    else:
      return func(request, owner_name, *args, **kwargs)
  return _loggedin_and_owner_required


def add_base_template_context_data(d,visitor_name, owner_name):
  """Generate the context data needed for templates that inherit from
  the base template.
  
  'd': the dictionary of custom data for the context.
  'visitor_name': the username of the visitor ("None" if anonymous).
  'owner_name': the username of the owner.
  'demo': flag indicating whether the demo mode is activated
  'auto_update': flag indicating whether updating news is automatic or not.
  """
  d.update({
    'visitor_name' : visitor_name,
    'owner_name' : owner_name,
    'demo': settings.DEMO,
    'auto_update': settings.USE_CELERY,
  })
  return d

def is_request_a_form_POST(request):
  """Guesses whether the request comes from a form's POST action.
  Assumes the form is built with Django's conventions."""
  return request.POST and u"next" in request.POST

def clean_checkbox_value(request, post_data, checkbox_name, current_value):
  """Chose between leaving the current_value untouched or considering it
  changed to False for a checkbox field, handling the case when is it
  not present in a form's POST data."""
  if checkbox_name not in post_data:
    if is_request_a_form_POST(request):
      # For a form's POST, the unchecked checkbox won't appear in
      # the request
      post_data[checkbox_name] = False
    else:
      # In other kind of posts, the absence of value means to keep
      # the original one unchanged.
      post_data[checkbox_name] = current_value

  
  
def home(request):

  """
  Return the home page of the site.
  """
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])
  d = add_base_template_context_data({},
                                     request.user.username,
                                     request.user.username)
  return render_to_response('home.html',d,
                            context_instance=RequestContext(request))


def request_for_update(request):
  """Trigger the collection of news from all known feeds and the cleanup
  of all references that have never been saved (past an arbitrary
  delay).
  """
  delete_old_references(datetime.now(timezone.utc)-NEWS_TIME_THRESHOLD)
  collect_news_from_feeds()
  if settings.DEMO:
    # keep only a short number of refs (the most recent) to avoid bloating the demo
    with transaction.commit_on_success():
      for ref in list(Reference.objects\
                      .filter(save_count=0)\
                      .order_by("-pub_date")[MAX_ITEMS_PER_PAGE:]):
        ref.delete()
  return HttpResponseRedirect(reverse("wom_user.views.home"))


def request_for_cleanup(request):
  """Trigger a cleanup of all references that have never been saved
  (past an arbitrary delay).
  """
  delete_old_references(datetime.now(timezone.utc)-NEWS_TIME_THRESHOLD)
  return HttpResponseRedirect(reverse("wom_user.views.home"))



def get_robots_txt(request):
  """Generate a set of robots.txt rules.""" 
  return HttpResponse("""
User-agent: *
Disallow: /u/*/river
Disallow: /u/*/sieve
Disallow: /accounts
""",mimetype='text/plain')

def get_humans_txt(request):
  """Generate a set of humans.txt rules. See also http://humanstxt.org/."""
  
  return HttpResponse("""
%s  

%s
  
/* SITE */
  Standards: HTML5, CSS3
  Platform: WaterOnMars
  Sources: https://github.com/tibonihoo/wateronmars
  License: Affero GPLv3
  Components: Twitter Bootstrap, mousetrap.js, jQuery, Infinite Ajax Scroll, TouchSwipe-Jquery-Plugin.
  Software: Django, Emacs, Firefox, Firebug, Inkscape
""" % (HUMANS_TEAM, HUMANS_THANKS),mimetype='text/plain')

  
def generate_collection_add_bookmarklet(base_url_with_domain,owner_name):
  return r"javascript:ref=location.href;selection%%20=%%20''%%20+%%20(window.getSelection%%20?%%20window.getSelection()%%20:%%20document.getSelection%%20?%%20document.getSelection()%%20%%20:%%20document.selection.createRange().text);t=document.title;window.location.href='%s%s?url='+encodeURIComponent(ref)+'&title='+encodeURIComponent(t)+'&comment='+encodeURIComponent(selection);" % (base_url_with_domain.rstrip("/"),reverse('wom_user.views.user_collection_add',args=(owner_name,)))


def generate_source_add_bookmarklet(base_url_with_domain,owner_name):
  return r"javascript:ref=location.href;t=document.title;window.location.href='%s%s?url='+encodeURIComponent(ref)+'&title='+encodeURIComponent(t);" % (base_url_with_domain.rstrip("/"),reverse('wom_user.views.user_river_source_add',args=(owner_name,)))


class CustomErrorList(ErrorList):
  """Customize errors display in forms to use Bootstrap classes."""
  def __unicode__(self):
    return self.as_span()
  def as_span(self):
    if not self: return u''
    return u'<span class="help-inline">%s</span>' \
      % ''.join([ unicode(e) for e in self])


@login_required(login_url=settings.LOGIN_URL)
@csrf_protect
def user_creation(request):
  if not request.user.is_staff:
    return HttpResponseForbidden("Sorry, you're not allowed to create new users.")
  if request.method == 'POST':
    form = UserProfileCreationForm(request.POST, error_class=CustomErrorList)
    if form.is_valid():
      form.save()
      return HttpResponseRedirect(reverse('wom_user.views.user_profile',
                                          args=(request.user.username,)))
  elif request.method == 'GET':
    form = UserProfileCreationForm(error_class=CustomErrorList)
  else:
    return HttpResponseNotAllowed(['GET','POST'])
  return render_to_response('user_creation.html',
                            {'form': form},
                            context_instance=RequestContext(request))


@login_required(login_url=settings.LOGIN_URL)
@csrf_protect
def user_profile(request):
  d =  add_base_template_context_data(
    {
      'username': request.user.username,
      'opml_form': OPMLFileUploadForm(error_class=CustomErrorList),
      'nsbmk_form': NSBookmarkFileUploadForm(error_class=CustomErrorList),
      'collection_add_bookmarklet': generate_collection_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
      'source_add_bookmarklet': generate_source_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
      'is_superuser': request.user.is_superuser,
      },request.user.username,request.user.username)
  return render_to_response('profile.html', d,
                            context_instance=RequestContext(request))


def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse("wom_user.views.home"))

def user_root(request,owner_name):
  return HttpResponseRedirect(reverse("wom_user.views.user_river_view", args=(owner_name,)))


def handle_uploaded_opml(opmlUploadedFile,user):
  if opmlUploadedFile.name.endswith(".opml") \
     or opmlUploadedFile.name.endswith(".xml"):
    import_user_feedsources_from_opml(user,opmlUploadedFile.read())
  else:
    raise ValueError("Uploaded file '%s' is not OPML !" % opmlUploadedFile.name)
    

@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_upload_opml(request,owner_name):
  if settings.DEMO:
    return HttpResponseForbidden("Uploading sources from OPML is disabled in DEMO mode.")
  if request.method == 'POST':
    form = OPMLFileUploadForm(request.POST, request.FILES,
                              error_class=CustomErrorList)
    if form.is_valid():
      handle_uploaded_opml(request.FILES['opml_file'],user=request.user)
      return HttpResponseRedirect(reverse("wom_user.views.user_river_sources",
                                          args=(request.user.username,)))
  else:
    form = OPMLFileUploadForm(error_class=CustomErrorList)
  d = add_base_template_context_data({'form': form},
                                     request.user.username,
                                     request.user.username)
  return render_to_response('opml_upload.html',d,
                            context_instance=RequestContext(request))





def handle_uploaded_nsbmk(nsbmkUploadedFile,user):
  if nsbmkUploadedFile.name.endswith(".html") \
     or nsbmkUploadedFile.name.endswith(".htm"):
    import_user_bookmarks_from_ns_list(user,nsbmkUploadedFile.read())
  else:
    raise ValueError("Uploaded file '%s' is not a Netscape-style bookmarks file !"\
                     % nsbmkUploadedFile.name)


@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_upload_nsbmk(request,owner_name):
  if settings.DEMO:
    return HttpResponseForbidden("Uploading bookmarks from NS bookmark list is disabled in DEMO mode.")
  if request.method == 'POST':
    form = NSBookmarkFileUploadForm(request.POST, request.FILES,
                                    error_class=CustomErrorList)
    if form.is_valid():
      handle_uploaded_nsbmk(request.FILES['bookmarks_file'],user=request.user)
      return HttpResponseRedirect(reverse("wom_user.views.user_collection",
                                          args=(request.user.username,)))
  else:
    form = NSBookmarkFileUploadForm(error_class=CustomErrorList)
  d = add_base_template_context_data({'form': form},
                                     request.user.username,
                                     request.user.username)
  return render_to_response('nsbmk_upload.html',d,
                            context_instance=RequestContext(request))


@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_river_source_add(request,owner_name):
  """Handle bookmarlet and form-based addition of a syndication of source.
  The bookmarlet is formatted in the following way:
  .../source/add/?{0}
  """.format('="..."&'.join(UserSourceAdditionForm.base_fields.keys()))
  if settings.DEMO:
    return HttpResponseForbidden("Source addition is not possible in DEMO mode.")
  if request.method == 'POST':
    src_info = request.POST
  elif request.GET: # GET
    src_info = dict( (k,urlunquote_plus(v.encode("utf-8"))) for k,v in request.GET.items())
  else:
    src_info = None
  form = UserSourceAdditionForm(request.user, src_info,
                                error_class=CustomErrorList)
  if src_info and form.is_valid():
    form.save()
    return HttpResponseRedirect(reverse('wom_user.views.user_river_sources',
                                        args=(request.user.username,)))
  d = add_base_template_context_data(
    {'form': form,
     'REST_PARAMS': ','.join(UserSourceAdditionForm.base_fields.keys())},
    request.user.username,request.user.username)
  return render_to_response('source_addition.html',d,
                            context_instance=RequestContext(request))


@loggedin_and_owner_required
@require_http_methods(["GET"])
def user_tributary(request, owner_name):
  # FUTURE: if there is more than twitter plugged in, display a list of possible tributaries
  return HttpResponseRedirect(reverse('wom_user.views.user_tributary_twitter', args=(request.user.username,)))

@loggedin_and_owner_required
@require_http_methods(["GET"])
def user_tributary_twitter(request, owner_name):
  if request.user != request.owner_user:
    return HttpResponseForbidden()
  owner_profile = request.owner_user.userprofile
  twitter_feeds = (GeneratedFeed.objects
    .filter(userprofile=owner_profile, twittertimeline__isnull=False)
    .select_related("twittertimeline")
    .order_by('-last_update_check', 'title')
  )

  class TwitterTimelineInfo:
    def __init__(self, feed, timeline, num_items_last_hour):
      self.feed = feed
      self.timeline = timeline
      self.num_items_last_hour = num_items_last_hour
    
  def get_twitter_timelines_info(feeds):
    [f.twittertimeline for f in feeds.all()]
    for idx,f in enumerate(feeds):
      yield TwitterTimelineInfo(f, f.twittertimeline, idx*10)
  twitter_timelines_summary = get_twitter_timelines_info(twitter_feeds.all())
  d = add_base_template_context_data({
    'twitter_timelines_summary': twitter_timelines_summary,
    'twitter_consent_link': "https://mouf"
  }, request.user.username, owner_name)
  return render_to_response('tributary_twitter.html',d,
                            context_instance=RequestContext(request))

@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_tributary_twitter_add(request,owner_name):
  """Handle bookmarlet and form-based addition of a twitter feed as a source.
  The bookmarlet is formatted in the following way:
  .../add?{0}
  """.format('="..."&'.join(UserTwitterSourceAdditionForm.base_fields.keys()))
  if settings.DEMO:
    return HttpResponseForbidden("Source addition is not possible in DEMO mode.")
  if request.method == 'POST':
    src_info = request.POST
  elif request.GET: # GET
    src_info = dict( (k,urlunquote_plus(v.encode("utf-8"))) for k,v in request.GET.items())
  else:
    src_info = None
  form = UserTwitterSourceAdditionForm(
    request.user, src_info,
    error_class=CustomErrorList)
  if src_info and form.is_valid():
    form.save()
    # TODO: Consider redirecting to twitter auth here !
    return HttpResponseRedirect(reverse('wom_user.views.user_river_sources', args=(request.user.username,)))
  d = add_base_template_context_data(
    {'form': form,
     'REST_PARAMS': ','.join(UserTwitterSourceAdditionForm.base_fields.keys())},
    request.user.username,request.user.username)
  return render_to_response('twitter_source_addition.html',d,
                            context_instance=RequestContext(request))

def prepare_reference_form(request, reference_url, reference_query_set):
  """Return a tuple: (reference, form) with the form showing all
  editable fields of a reference identified by its url.

  May raise Reference.DoesNotExist if no reference with the given url
  could be found or ValueError if the request is a POST with a badly
  formatted body.
  """
  form_data = []
  if request.POST:
    if is_request_a_form_POST(request):
      form_data.append(request.POST.copy())
    else:
      try:
        src_info = simplejson.loads(request.body)
      except Exception:
        src_info = {}
      if not src_info:
        raise ValueError("Only a JSON formatted non-empty request is accepted.")
      form_data.append(src_info)
  reference = reference_query_set.get(url=reference_url)
  if form_data and "ref-pub_date" not in form_data[0]:
    form_data[0]["ref-pub_date"] = reference.pub_date
  if form_data and "ref-description" not in form_data[0]:
    form_data[0]["ref-description"] = reference.description or " "
  if form_data and "ref-title" not in form_data[0]:
    form_data[0]["ref-title"] = reference.title
  return reference, ReferenceEditForm(*form_data, instance=reference,
                                      error_class = CustomErrorList,
                                      prefix = "ref"), form_data

@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_river_source_item(request, owner_name, source_url):
  """Generate an editable view of a given source identified by its url."""
  owner_profile = request.owner_user.userprofile
  try:
    reference, form, form_data = prepare_reference_form(request, source_url,
                                                        owner_profile.sources)
  except Reference.DoesNotExist:
    return HttpResponseNotFound()
  except ValueError, e:
    return HttpResponseBadRequest(str(e))
  feedForms = {}
  for idx,feed in enumerate(WebFeed.objects.filter(source__url=source_url)):
    currentPrefix = "feed{0}".format(idx)
    initial = {"follow": feed in owner_profile.web_feeds.all()}
    followFieldName = currentPrefix+"-follow"
    if form_data:
      clean_checkbox_value(request, form_data[0], followFieldName, initial["follow"])
    feedForms[feed.xmlURL] = WebFeedOptInOutForm(request.owner_user,feed,
                                                 *form_data, error_class = CustomErrorList,
                                                 prefix=currentPrefix, initial=initial)
  # TODO: add forms of generated_feeds if any
  def optOutFormsAreValid():
    return reduce(lambda currentValidity, nextForm: currentValidity and nextForm.is_valid(), feedForms.values(), True)
  def optOutFormsSave():
    return [f.save() for f in feedForms.values()]
  if request.POST:
    if settings.DEMO:
      return HttpResponseForbidden("Source editting is not possible in DEMO mode.")
    if form.is_valid() and optOutFormsAreValid():
      form.save()
      optOutFormsSave()
      return HttpResponseRedirect(reverse('wom_user.views.user_river_source_item',
                                          args=(request.user.username, source_url)))
  d = add_base_template_context_data(
    { 
      'ref_form': form,
      'feed_forms': feedForms,
      'ref_url': source_url,
      'ref_title': reference.title,
    },
    request.user.username,request.user.username)
  return render_to_response('source_edit.html',d,
                            context_instance=RequestContext(request))

@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_collection_add(request,owner_name):
  """Handle bookmarlet and form-based addition of a bookmark.
  The bookmarlet is formatted in the following way:
  .../collection/add/?{0}
  """.format('="..."&'.join(UserBookmarkAdditionForm.base_fields.keys()))
  if settings.DEMO:
    return HttpResponseForbidden("Bookmark addition is not possible in DEMO mode.")
  if request.method == 'POST':
    bmk_info = request.POST
  elif request.GET: # GET
    bmk_info = dict( (k,urlunquote_plus(v.encode("utf-8"))) for k,v in request.GET.items())
  else:
    bmk_info = None
  form = UserBookmarkAdditionForm(request.user, bmk_info, error_class=CustomErrorList)
  if bmk_info and form.is_valid():
    form.save()
    return HttpResponseRedirect(reverse('wom_user.views.user_collection',
                                        args=(request.user.username,)))
  d = add_base_template_context_data(
    {'form': form,
     'REST_PARAMS': ','.join(UserBookmarkAdditionForm.base_fields.keys())},
    request.user.username,request.user.username)
  return render_to_response('bookmark_addition.html',d,
                            context_instance=RequestContext(request))
  

@loggedin_and_owner_required
@csrf_protect
def post_to_user_collection(request,owner_name):
  """Add an item with the payload from a form's POST or with the
  following JSON payload::  
    { "url": "<url>",
      "title": "the title", // optional but recommended
      "comment": "", // optional
      "source_url": "<url>", // optional
      "source_title": "the name", // optional
    }
  """
  if settings.DEMO:
    return HttpResponseForbidden("Bookmark addition is not possible in DEMO mode.")
  try:
    bmk_info = simplejson.loads(request.body)
  except Exception:
    bmk_info = {}
  if not u"url" in bmk_info:
    return HttpResponseBadRequest("Only a JSON formatted request with a 'url' parameter is accepted.")
  form = UserBookmarkAdditionForm(request.user, bmk_info)
  response_dict = {}
  if form.is_valid():
    form.save()
    response_dict["status"] = u"success"
    # TODO: also add the url to the new bookmark in the answer
  else:
    response_dict["status"] = u"error"
    response_dict["form_fields_ul"] = form.as_ul()
  return HttpResponse(simplejson.dumps(response_dict),
                      mimetype='application/json')


@check_and_set_owner
def get_user_collection(request,owner_name):
  """Display the collection of bookmarks"""
  bookmarks = UserBookmark.objects.filter(owner=request.owner_user)\
                                  .select_related("reference").all()
  if request.user!=request.owner_user:
    bookmarks = bookmarks.filter(is_public=True)
  bookmarks = bookmarks.order_by('-saved_date')
  expectedFormat = request.GET.get("format","html").lower()
  if expectedFormat=="ns-bmk-list":
    paginator = Paginator(bookmarks, bookmarks.count())
  else:
    paginator = Paginator(bookmarks, MAX_ITEMS_PER_PAGE)
  page = request.GET.get('page')
  try:
    bookmarks = paginator.page(page)
  except (PageNotAnInteger,EmptyPage):
    # If page is not an integer or out of range, deliver first page.
    bookmarks = paginator.page(1)
  d = add_base_template_context_data(
    {
      'user_bookmarks': bookmarks,
      'num_bookmarks': bookmarks.count,
      'collection_url' : request.build_absolute_uri(request.path).rstrip("/"),
      'collection_add_bookmarklet': generate_collection_add_bookmarklet(
        request.build_absolute_uri("/"),request.user.username),
      }, request.user.username, owner_name)
  if expectedFormat=="ns-bmk-list":
    return render_to_response('collection_nsbmk.html',d,
                              context_instance=RequestContext(request),
                              mimetype="text/html")
  else:
    return render_to_response('collection.html',d,
                              context_instance=RequestContext(request))


def user_collection(request,owner_name):
  if request.method == 'GET':
    return get_user_collection(request,owner_name)
  elif request.method == 'POST':
    if request.user.username != owner_name:
      return HttpResponseForbidden()
    return post_to_user_collection(request,owner_name)
  else:
    return HttpResponseNotAllowed(['GET','POST'])


@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_collection_item(request, owner_name, reference_url):
  """Generate an editable view of a given reference identified by its url."""
  try:
    reference, form, form_data = prepare_reference_form(request, reference_url,
                                                        Reference.objects\
                                                        .filter(userbookmark__owner\
                                                                =request.user))
  except Reference.DoesNotExist:
    return HttpResponseNotFound()
  except ValueError, e:
    return HttpResponseBadRequest(str(e))
  bookmark = UserBookmark.objects.get(owner=request.owner_user, reference__url=reference_url)
  if form_data:
    if "bmk-comment" not in form_data[0]:
      form_data[0]["bmk-comment"] = bookmark.comment or " "
    clean_checkbox_value(request, form_data[0], "bmk-is_public", bookmark.is_public)
  bmk_form = UserBookmarkEditForm(*form_data, instance=bookmark,
                                  error_class = CustomErrorList,
                                  prefix = "bmk")
  if request.POST:
    if settings.DEMO:
      return HttpResponseForbidden("Reference editting is not possible in DEMO mode.")
    if form.is_valid() and bmk_form.is_valid():
      form.save()
      bmk_form.save()
      return HttpResponseRedirect(reverse('wom_user.views.user_collection_item',
                                          args=(request.user.username, reference_url)))
  d = add_base_template_context_data(
    { 
      'bmk_form': bmk_form,
      'ref_form': form,
      'ref_url': reference_url,
      'ref_title': reference.title,
      'ref_sources': sorted(bookmark.get_sources()),
      'ref_tags': sorted(bookmark.get_tag_names())
    },
    request.user.username,request.user.username)
  return render_to_response('bookmark_edit.html',d,
                            context_instance=RequestContext(request))


@check_and_set_owner
def user_river_view(request,owner_name):
  check_user_unread_feed_items(request.owner_user)
  river_items = ReferenceUserStatus.objects\
                                   .filter(owner=request.owner_user)\
                                   .order_by('-reference_pub_date')\
                                   .select_related("reference")
  paginator = Paginator(river_items, MAX_ITEMS_PER_PAGE)
  page = request.GET.get('page')
  try:
    news_items = paginator.page(page)
  except (PageNotAnInteger,EmptyPage):
    # If page is not an integer or out of range, deliver first page.
    news_items = paginator.page(1)
  d = add_base_template_context_data({
    'news_items': news_items,
    'source_add_bookmarklet': generate_source_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
  }, request.user.username, owner_name)
  return render_to_response('river.html',d,
                            context_instance=RequestContext(request))


def generate_user_sieve(request,owner_name):
  """
  Generate the HTML page on which a given user will be able to see and
  use its sieve to read and sort out the latests news.
  """
  check_user_unread_feed_items(request.owner_user)
  unread_references = ReferenceUserStatus.objects.filter(owner=request.owner_user,
                                                         has_been_read=False)
  num_unread = unread_references.count()
  oldest_unread_references = unread_references.order_by('reference_pub_date')\
                             [:MAX_ITEMS_PER_PAGE]\
                               .select_related("reference","main_source")
  d = add_base_template_context_data({
      'oldest_unread_references': oldest_unread_references,
      'num_unread_references': num_unread,
      'user_collection_url': reverse("wom_user.views.user_collection",
                                     args=(request.user.username,)),
      'source_add_bookmarklet': generate_source_add_bookmarklet(
        request.build_absolute_uri("/"),request.user.username),
      }, request.user.username, request.user.username)
  return render_to_response('sieve.html',d,
                            context_instance=RequestContext(request))


def apply_to_user_sieve(request,owner_name):
  """
  Act on the items passing through the sieve.
  
  The accepted actions are to mark items as read, with the
  following JSON payload::
  
    { "action" = "read",
      "references" = [ "<url1>", "<url2>", ...],
    }

  or to mark all items as read:
  
    { "action" = "drop" }
  """
  if settings.DEMO:
    return HttpResponseForbidden("Changing the sieve's state is not possible in DEMO mode.")
  try:
    action_dict = simplejson.loads(request.body)
  except:
    action_dict = {}
  action_name = action_dict.get(u"action")
  if action_name not in (u"read", u"drop"):
    return HttpResponseBadRequest("Only a JSON formatted 'read' and 'drop' actions are supported.")
  modified_rust = []
  rust_iterator = ReferenceUserStatus.objects\
                                      .filter(has_been_read=False,
                                              owner=request.owner_user)
  if action_name == u"read":
    target_urls = action_dict.get(u"references",[])
    rust_iterator = rust_iterator.filter(reference__url__in=target_urls)
  for rust in rust_iterator:
    rust.has_been_read = True
    modified_rust.append(rust)
  with transaction.commit_on_success():
    for r in modified_rust:
      r.save()
  count = len(modified_rust)
  response_dict = {u"action": action_name, u"status": u"success", u"count": count}
  return HttpResponse(simplejson.dumps(response_dict), mimetype='application/json')

  

@loggedin_and_owner_required
def user_river_sieve(request,owner_name):
  if request.owner_user != request.user:
    return HttpResponseForbidden()
  if request.method == 'GET':
    return generate_user_sieve(request,owner_name)
  elif request.method == 'POST':
    return apply_to_user_sieve(request, owner_name)
  else:
    return HttpResponseNotAllowed(['GET','POST'])


  
@check_and_set_owner
def user_river_sources(request,owner_name):
  if request.method == 'GET':
    owner_profile = request.owner_user.userprofile
    web_feeds = owner_profile.web_feeds.all()\
                                       .order_by('source__title')\
                                       .select_related("source")
    if request.user == request.owner_user:
      other_sources = owner_profile.sources.all()
    else:
      other_sources = owner_profile.public_sources.all()
    other_sources = other_sources.exclude(webfeed__userprofile=owner_profile)\
                                 .order_by("title")
    def add_tag_to_feed(feed):
      tag_names = get_item_tag_names(request.owner_user,feed)
      feed.main_tag_name = tag_names[0] if tag_names else ""
      return feed
    web_feeds = [add_tag_to_feed(f) for f in web_feeds.iterator()]
    web_feeds.sort(key=lambda f:f.main_tag_name)
    d = add_base_template_context_data({
        'tagged_web_feeds': web_feeds,
        'user_tags': get_user_tags(request.owner_user), 
        'other_sources': other_sources,
        'num_sources' : len(web_feeds)+other_sources.count(),
        'source_add_bookmarklet': generate_source_add_bookmarklet(
          request.build_absolute_uri("/"),request.user.username),
        }, request.user.username, owner_name)
    expectedFormat = request.GET.get("format","html")
    if expectedFormat.lower()=="opml":
      return render_to_response('sources_opml.xml',d,
                                context_instance=RequestContext(request),
                                mimetype="text/xml")
    else:
      return render_to_response('sources.html',d,
                                context_instance=RequestContext(request))
  elif request.user != request.owner_user:
    return HttpResponseForbidden()
  elif request.method == 'POST':
    try:
      src_info = simplejson.loads(request.body)
    except Exception:
      src_info = {}
    if not u"url" in src_info:
      return HttpResponseBadRequest("Only a JSON formatted request with a 'url' parameter is accepted.")
    q = QueryDict('', mutable=True)
    q.update(src_info)
    request.POST = q
    return user_river_source_add(request, owner_name)
  else:
    return HttpResponseNotAllowed(['GET','POST'])

