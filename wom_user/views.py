import urllib

from django.template import RequestContext
from django.core.urlresolvers import reverse

from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound

from django.shortcuts import render_to_response
from django.utils import simplejson
from django.forms.util import ErrorList


from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from wateronmars.views import wom_add_base_context_data

from wom_user.forms import OPMLFileUploadForm
from wom_user.forms import NSBookmarkFileUploadForm
from wom_user.forms import UserProfileCreationForm
from wom_user.forms import UserBookmarkAdditionForm
from wom_user.forms import UserSourceAdditionForm
from wom_user.forms import CreateUserSourceRemovalForm

from wom_user.models import UserBookmark

from wom_river.tasks import opml2db
from wom_river.tasks import nsbmk2db

def check_and_set_owner(func):
  """Decorator that applies to functions expecting the "owner" name as a second argument.

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
  """Decorator that applies to functions expecting the "owner" name as a second argument.

  It will check that the visitor is also considered as the owner of the resource it is accessing.

  Note: automatically calls login_required and check_and_set_owner decorators.
  """
  # TODO when not logged in send a 401 authentication requested and
  # implement corresponding template (at least send a 401 for non-GET
  # requests !)
  @login_required(login_url='/accounts/login/')
  @check_and_set_owner
  def _loggedin_and_owner_required(request, owner_name, *args, **kwargs):
    if request.user != request.owner_user:
      return HttpResponseForbidden()
    else:
      return func(request, owner_name, *args, **kwargs)
  return _loggedin_and_owner_required


def generate_collection_add_bookmarklet(base_url_with_domain,owner_name):
  return r"javascript:ref=location.href;selection%%20=%%20''%%20+%%20(window.getSelection%%20?%%20window.getSelection()%%20:%%20document.getSelection%%20?%%20document.getSelection()%%20%%20:%%20document.selection.createRange().text);t=document.title;window.location.href='%s%s?url='+encodeURIComponent(ref)+'&title='+encodeURIComponent(t)+'&description='+encodeURIComponent(selection);" % (base_url_with_domain.rstrip("/"),reverse('wom_user.views.user_collection_add',args=(owner_name,)))

def generate_source_add_bookmarklet(base_url_with_domain,owner_name):
  return r"javascript:ref=location.href;t=document.title;window.location.href='%s%s?url='+encodeURIComponent(ref)+'&name='+encodeURIComponent(t);" % (base_url_with_domain.rstrip("/"),reverse('wom_user.views.user_river_source_add',args=(owner_name,)))

class CustomErrorList(ErrorList):
  """Customize errors display in forms to use Bootstrap classes."""
  def __unicode__(self):
    return self.as_span()
  def as_span(self):
    if not self: return u''
    return u'<span class="help-inline">%s</span>' % ''.join([ unicode(e) for e in self])


@login_required(login_url='/accounts/login/')
@csrf_protect
def user_profile(request):
  d =  wom_add_base_context_data(
    {
      'username': request.user.username,
      'opml_form': OPMLFileUploadForm(error_class=CustomErrorList),
      'nsbmk_form': NSBookmarkFileUploadForm(error_class=CustomErrorList),
      'collection_add_bookmarklet': generate_collection_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
      'source_add_bookmarklet': generate_source_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
      },request.user.username,request.user.username)
  return render_to_response('wom_user/profile.html', d, context_instance=RequestContext(request))


def handle_uploaded_opml(opmlUploadedFile,user):
  if opmlUploadedFile.name.endswith(".opml") or opmlUploadedFile.name.endswith(".xml"):
    opml2db(opmlUploadedFile.read(),isPath=False,
            user_profile=user.userprofile)
  else:
    raise ValueError("Uploaded file '%s' is not OPML !" % opmlUploadedFile.name)
  

@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_upload_opml(request,owner_name):
  if request.method == 'POST':
    form = OPMLFileUploadForm(request.POST, request.FILES, error_class=CustomErrorList)
    if form.is_valid():
      handle_uploaded_opml(request.FILES['opml_file'],user=request.user)
      return HttpResponseRedirect('/u/%s/sources' % request.user.username)
  else:
    form = OPMLFileUploadForm(error_class=CustomErrorList)
  d = wom_add_base_context_data({'form': form},request.user.username,request.user.username)
  return render_to_response('wom_user/opml_upload.html',d, context_instance=RequestContext(request))





def handle_uploaded_nsbmk(nsbmkUploadedFile,user):
  if nsbmkUploadedFile.name.endswith(".html") or nsbmkUploadedFile.name.endswith(".htm"):
    nsbmk2db(nsbmkUploadedFile.read(),user=user)
  else:
    raise ValueError("Uploaded file '%s' is not a Netscape-style bookmarks file !" % nsbmkUploadedFile.name)
  

@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_upload_nsbmk(request,owner_name):
  if request.method == 'POST':
    form = NSBookmarkFileUploadForm(request.POST, request.FILES, error_class=CustomErrorList)
    if form.is_valid():
      handle_uploaded_nsbmk(request.FILES['bookmarks_file'],user=request.user)
      return HttpResponseRedirect('/u/%s/collection' % request.user.username)
  else:
    form = NSBookmarkFileUploadForm(error_class=CustomErrorList)
  d = wom_add_base_context_data({'form': form},request.user.username,request.user.username)
  return render_to_response('wom_user/nsbmk_upload.html',d, context_instance=RequestContext(request))


@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_river_source_add(request,owner_name):
  """Handle bookmarlet and form-based addition of a syndication of source.
  The bookmarlet is formatted in the following way:
  .../source/add/?url="..."&name="..."&feed_url="..."
  """
  if request.method == 'POST':
    try:
      src_info = simplejson.loads(request.body)
    except Exception,e:
      src_info = {}
      print e
    if not u"url" in src_info:
      return HttpResponseBadRequest("Only a JSON formatted request with a 'url' parameter is accepted.")
  elif request.GET: # GET
    src_info = dict( (k,urllib.unquote_plus(v.encode("utf-8"))) for k,v in request.GET.items())
  else:
    src_info = None
  form = UserSourceAdditionForm(request.user, src_info,
                                error_class=CustomErrorList)
  if src_info and form.is_valid():
    form.save()
    return HttpResponseRedirect('/u/%s/sources/' % request.user.username)
  d = wom_add_base_context_data({'form': form},request.user.username,request.user.username)
  return render_to_response('wom_user/source_addition.html',d, context_instance=RequestContext(request))


@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_river_source_remove(request,owner_name):
  """Stop subscriptions to sources via a form only !"""
  if request.method == 'POST':
    src_info = request.POST
  elif request.GET: # GET
    src_info = dict( (k,urllib.unquote_plus(v.encode("utf-8"))) for k,v in request.GET.items())
  else:
    src_info = None
  form = CreateUserSourceRemovalForm(request.user, src_info, error_class=CustomErrorList)
  if src_info and form.is_valid():
    form.save()
    return HttpResponseRedirect('/u/%s/sources/' % request.user.username)
  d = wom_add_base_context_data({'form': form},request.user.username,request.user.username)
  return render_to_response('wom_user/source_removal.html',d, context_instance=RequestContext(request))


@loggedin_and_owner_required
@csrf_protect
@require_http_methods(["GET","POST"])
def user_collection_add(request,owner_name):
  """Handle bookmarlet and form-based addition of a bookmark.
  The bookmarlet is formatted in the following way:
  .../collection/add/?url="..."&title="..."&description="..."&source_url="..."&source_name="..."&pub_date="..."
  """
  if request.method == 'POST':
    bmk_info = request.POST
  elif request.GET: # GET
    bmk_info = dict( (k,urllib.unquote_plus(v.encode("utf-8"))) for k,v in request.GET.items())
  else:
    bmk_info = None
  form = UserBookmarkAdditionForm(request.user, bmk_info, error_class=CustomErrorList)
  if form.is_valid():
    form.save()
    return HttpResponseRedirect('/u/%s/collection' % request.user.username)
  d = wom_add_base_context_data({'form': form},request.user.username,request.user.username)
  return render_to_response('wom_user/bookmark_addition.html',d, context_instance=RequestContext(request))
  
  
@loggedin_and_owner_required
@csrf_protect
def post_to_user_collection(request,owner_name):
  """Add an item with the payload from a form's POST or with the
  following JSON payload::  
    { "url": "<url>",
      "title": "the title", // optional but recommended
      "description": "", // optional
      "source_url": "<url>", // optional
      "source_name": "the name", // optional
    }
  """
  try:
    bmk_info = simplejson.loads(request.body)
  except Exception,e:
    bmk_info = {}
    print e
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
  return HttpResponse(simplejson.dumps(response_dict), mimetype='application/json')

    
@check_and_set_owner
def get_user_collection(request,owner_name):
  """Display the collection of bookmarks"""
  bookmarks = UserBookmark.objects.filter(owner=request.owner_user).select_related("reference").all()
  # TODO preload sources ?
  d = wom_add_base_context_data(
    {
      'user_bookmarks': bookmarks,
      'num_bookmarks': len(bookmarks),
      'collection_url' : request.build_absolute_uri(request.path).rstrip("/"),
      'collection_add_bookmarklet': generate_collection_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
      }, request.user.username, owner_name)
  return render_to_response('wom_user/collection.html_dt',d, context_instance=RequestContext(request))


def user_collection(request,owner_name):
  if request.method == 'GET':
    return get_user_collection(request,owner_name)
  elif request.method == 'POST':
    if request.user.username != owner_name:
      return HttpResponseForbidden()
    return post_to_user_collection(request,owner_name)
  else:
    return HttpResponseNotAllowed(['GET','POST'])




@login_required(login_url='/accounts/login/')
@csrf_protect
def user_creation(request):
  if not request.user.is_staff:
    return HttpResponseForbidden()
  if request.method == 'POST':
    form = UserProfileCreationForm(request.POST, error_class=CustomErrorList)
    if form.is_valid():
      form.save()
      return HttpResponseRedirect('/accounts/profile')
  elif request.method == 'GET':
    form = UserProfileCreationForm(error_class=CustomErrorList)
  else:
    return HttpResponseNotAllowed(['GET','POST'])
  return render_to_response('registration/user_creation.html',
                            {'form': form}, context_instance=RequestContext(request))

