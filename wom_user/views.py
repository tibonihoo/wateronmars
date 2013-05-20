from urlparse import urlparse

from django.template import Context, loader
from django.template import RequestContext

from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect

import datetime
from django.utils import timezone
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.db import transaction


from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from wom_pebbles.models import Reference
from wom_pebbles.models import Source
from wom_user.models import UserBookmark
from wom_river.models import ReferenceUserStatus

from django import forms
from wom_river.tasks import opml2db


@login_required(login_url='/accounts/login/')
def user_profile(request):
  t = loader.get_template('wom_user/profile.html')
  c = Context({
      'username': request.user.username,
      })
  return HttpResponse(t.render(c))


def handle_uploaded_opml(opmlUploadedFile,user):
  if opmlUploadedFile.name.endswith(".opml") or opmlUploadedFile.name.endswith(".xml"):
    opml2db(opmlUploadedFile.read(),isPath=False,
            user_profile=user.userprofile)
  else:
    raise ValueError("Uploaded file '%s' is not OPML !" % opmlUploadedFile.name)
  
class OPMLFileUploadForm(forms.Form):
    opml_file  = forms.FileField()


@login_required(login_url='/accounts/login/')
@csrf_protect
def user_upload_opml(request):
  if request.method == 'POST':
    form = OPMLFileUploadForm(request.POST, request.FILES)
    if form.is_valid():
      handle_uploaded_opml(request.FILES['opml_file'],user=request.user)
      return HttpResponseRedirect('/u/%s/sources' % request.user.username)
  else:
    form = OPMLFileUploadForm()
  return render_to_response('wom_user/opml_upload.html',
                            {'username':request.user.username,'form': form},
                            context_instance=RequestContext(request))


@login_required(login_url='/accounts/login/')
def post_to_user_collection(request):
  """
  Act on the items passing through the sieve.
  
  The only accepted action for now is to bookmark an items, with the
  following JSON payload::
  
    { "a": "add",
      "url": "<url>",
      "title": "the title", // optional but recommended
      "description": "", // optional
      "source_url": "<url>", // optional
      "source_name": "the name", // optional
    }
  """
  try:
    action_dict = simplejson.loads(request.body)
  except:
    action_dict = {}
  if action_dict.get(u"a") != u"add":
    return HttpResponseBadRequest("Only a JSON formatted 'save' action is supported.")
  if not u"url" in action_dict:
    return HttpResponseBadRequest("Impossible to 'save' a bookmark: the 'url' parameter is missing.")
  url_to_save = action_dict[u"url"]
  if not request.user.userbookmark_set.filter(reference__url=url_to_save).exists():
    # lookup a matching Reference
    same_url_refs = Reference.objects.filter(url=url_to_save)
    if u"source_url" in action_dict:
      bookmark_source_url = action_dict[u"source_url"]
    else:
      url_cpt = urlparse(url_to_save)
      bookmark_source_url = url_cpt.netloc or url_to_save
    same_sources = request.user.userprofile.sources.filter(url=bookmark_source_url).all()
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
        if u"source_name" in action_dict:
          bookmark_source_name = action_dict[u"source_name"]
        else:
          url_cpt = urlparse(url_to_save)
          bookmark_source_name = url_cpt.hostname or ""
          if url_cpt.path:
            bookmark_source_name +=  "/" + url_cpt.path
        bookmark_source = Source()
        bookmark_source.url = bookmark_source_url
        bookmark_source.name = bookmark_source_name
        bookmark_source.save()
      bookmarked_ref = Reference()
      bookmarked_ref.source = bookmark_source
      bookmarked_ref.url = action_dict[u"url"]
      bookmarked_ref.title = action_dict.get(u"title",bookmarked_ref.url)
      # for lack of a better source of info
      bookmarked_ref.pub_date = action_dict.get(u"pub_date",datetime.datetime.now(timezone.utc)-datetime.timedelta(weeks=12))
      bookmarked_ref.description = action_dict.get(u"description","")
      bookmarked_ref.tags = bookmark_source.tags
      bookmarked_ref.save()
    with transaction.commit_on_success():
      b = UserBookmark()
      b.owner = request.user
      b.saved_date = datetime.datetime.now(timezone.utc)-datetime.timedelta(weeks=12)
      b.reference = bookmarked_ref
      bookmarked_ref.save_count += 1
      b.save()
      bookmarked_ref.save()
    with transaction.commit_on_success():
      if not user_has_same_source:
        request.user.userprofile.sources.add(bookmarked_ref.source)
        request.user.userprofile.save()
      b.tags = bookmarked_ref.tags.all()
      b.save()
      
  with transaction.commit_on_success():
    for rust in ReferenceUserStatus.objects.filter(ref__url=url_to_save).all():
      rust.has_been_saved = True
      rust.save()
  response_dict = {u"a": u"save", u"status": u"success"}
  return HttpResponse(simplejson.dumps(response_dict), mimetype='application/json')

    
@login_required(login_url='/accounts/login/')
def get_user_collection(request):
  bookmarks = UserBookmark.objects.filter(owner=request.user).select_related("reference").all()
  # TODO preload sources !
  t = loader.get_template('wom_user/collection.html_dt')
  c = Context({
      'user_bookmarks': bookmarks,
      'username' : request.user.username,
      'num_bookmarks': len(bookmarks),
      'title_qualify': "Your",
      'realm': "u/%s" % request.user.username,
      'collection_url' : request.build_absolute_uri(request.path).rstrip("/")
      })
  return HttpResponse(t.render(c))


@login_required(login_url='/accounts/login/')
def user_collection(request):
  if request.method == 'GET':
    return get_user_collection(request)
  elif request.method == 'POST':
    print "received: %s" % request
    try:
      return post_to_user_collection(request)
    except Exception,e:
      print e
      raise e
  else:
    return HttpResponseNotAllowed(['GET','POST'])

