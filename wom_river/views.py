from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.utils import simplejson
from django.db import transaction

from django.template import RequestContext
from django.shortcuts import render_to_response

from wateronmars.views import wom_add_base_context_data
from wateronmars.views import WOMPublic

from wom_user.views import check_and_set_owner
from wom_user.views import loggedin_and_owner_required

from wom_pebbles.models import Reference
from wom_pebbles.models import Source
from wom_river.models import FeedSource
from wom_river.models import ReferenceUserStatus
from wom_river.tasks import check_user_unread_feed_items
from wom_river.tasks import generate_reference_user_status
from wom_user.views import generate_source_add_bookmarklet
from wom_user.views import user_river_source_add
from wom_user.views import user_river_source_remove

MAX_ITEMS_PER_PAGE = 100

def public_river_view(request):
  latest_unread_pebbles = Reference.objects.filter(is_public=True).order_by('-pub_date')[:MAX_ITEMS_PER_PAGE]
  d = wom_add_base_context_data({
      'latest_unread_pebbles': latest_unread_pebbles,
      }, request.user.username, WOMPublic)
  return render_to_response('wom_river/river.html_dt', d)


def public_river_sieve(request):
  unread_references = Reference.objects.filter(is_public=True)
  num_unread_references = unread_references.count()
  oldest_unread_references = unread_references.order_by('pub_date')[:MAX_ITEMS_PER_PAGE]
  if request.user.is_authenticated():
    user = request.user
    user_collection_url = "/u/%s/collection/" % user.username
  else:
    user = None
    user_collection_url = ""
  d = wom_add_base_context_data(
    {
      'oldest_unread_references': generate_reference_user_status(user,oldest_unread_references),
      'num_unread_references': num_unread_references,
      'user_collection_url': user_collection_url,
      }, request.user.username, WOMPublic)
  return render_to_response('wom_river/sieve.html_dt',d)

def public_river_sources(request):
  syndicated_sources = FeedSource.objects.filter(is_public=True).order_by('name')
  other_sources = Source.objects.filter(is_public=True).exclude(url__in=[s.url for s in syndicated_sources]).order_by('name')
  d = wom_add_base_context_data(
    {
      'syndicated_sources': syndicated_sources,
      'referenced_sources': other_sources,
      }, request.user.username, WOMPublic)
  return render_to_response('wom_river/river_sources.html_dt', d)

@check_and_set_owner
def user_river_view(request,owner_name):
  user_profile = request.owner_user.userprofile
  latest_items = []
  for source in user_profile.feed_sources.all():
    latest_items.extend(source.reference_set.order_by('-pub_date')[:MAX_ITEMS_PER_PAGE])
  latest_items.sort(key=lambda x:x.pub_date)
  latest_items.reverse()
  d = wom_add_base_context_data({
      # TODO rename to latest_references
      'latest_unread_references': latest_items[:MAX_ITEMS_PER_PAGE],
      'source_add_bookmarklet': generate_source_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
      }, request.user.username, owner_name)
  return render_to_response('wom_river/river.html_dt',d, context_instance=RequestContext(request))


def generate_user_sieve(request,owner_name):
  """
  Generate the HTML page on which a given user will be able to see and
  use it's sieve to read and sort out the latests news.
  """
  check_user_unread_feed_items(request.user)
  unread_references = ReferenceUserStatus.objects.filter(has_been_read=False)
  num_unread = unread_references.count()
  oldest_unread_references = unread_references.select_related("ref","source").order_by('ref_pub_date')[:MAX_ITEMS_PER_PAGE]
  d = wom_add_base_context_data({
      'oldest_unread_references': oldest_unread_references,
      'num_unread_references': num_unread,
      'user_collection_url': "/u/%s/collection/" % request.user.username,
      'source_add_bookmarklet': generate_source_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
      }, request.user.username, request.user.username)
  return render_to_response('wom_river/sieve.html_dt',d, context_instance=RequestContext(request))


def apply_to_user_sieve(request,owner_name):
  """
  Act on the items passing through the sieve.
  
  The only accepted action for now is to mark items as read, with the
  following JSON payload::
  
    { "action" = "read",
      "references" = [ "<url1>", "<url2>", ...],
    }
  """
  check_user_unread_feed_items(request.user)
  try:
    action_dict = simplejson.loads(request.body)
  except:
    action_dict = {}
  if action_dict.get(u"action") != u"read":
    return HttpResponseBadRequest("Only a JSON formatted 'read' action is supported.")
  modified_rust = []
  for read_url in action_dict.get(u"references",[]):
    for rust in ReferenceUserStatus.objects.filter(has_been_read=False,user=request.user).select_related("ref").all():
      if rust.ref.url == read_url:
        rust.has_been_read = True
        modified_rust.append(rust)
  with transaction.commit_on_success():
    for r in modified_rust:
      r.save()
  count = len(modified_rust)
  response_dict = {u"action": u"read", u"status": u"success", u"count": count}
  return HttpResponse(simplejson.dumps(response_dict), mimetype='application/json')

@loggedin_and_owner_required
def user_river_sieve(request,owner_name):
  if owner_name != request.user.username:
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
    syndicated_sources = owner_profile.feed_sources.all().order_by('name')
    visible_sources = owner_profile.sources
    other_sources = visible_sources.exclude(id__in=[s.id for s in syndicated_sources]).order_by("name")
    d = wom_add_base_context_data({
        'syndicated_sources': syndicated_sources,
        'referenced_sources': other_sources,
        'source_add_bookmarklet': generate_source_add_bookmarklet(request.build_absolute_uri("/"),request.user.username),
        }, request.user.username, owner_name)
    return render_to_response('wom_river/river_sources.html_dt',d, context_instance=RequestContext(request))
  elif owner_name != request.user.username:
      return HttpResponseForbidden()
  elif request.method == 'POST':
    return user_river_source_add(request, owner_name)
  # TODO
  # elif request.method == 'DELETE':
  #   request.method = "POST"
  #   return user_river_source_remove(request, owner_name)
  else:
    return HttpResponseNotAllowed(['GET','POST'])
  
