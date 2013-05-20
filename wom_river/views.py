from django.template import Context, loader
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.utils import simplejson
from django.db import transaction

from django.contrib.auth.decorators import login_required

from wom_pebbles.models import Reference
from wom_river.models import FeedSource
from wom_river.models import ReferenceUserStatus
from wom_river.tasks import check_user_unread_feed_items
from wom_river.tasks import generate_reference_user_status


MAX_ITEMS_PER_PAGE = 100

def public_river_view(request):
  latest_unread_pebbles = Reference.objects.filter(is_public=True).order_by('-pub_date')[:MAX_ITEMS_PER_PAGE]
  t = loader.get_template('wom_river/river.html_dt')
  if not latest_unread_pebbles:
    messages = ["No pebble yet !"]
  else:
    messages = []
  if request.user.is_authenticated():
    username = request.user.username
  else:
    username = None
  c = Context({
      'latest_unread_pebbles': latest_unread_pebbles,
      'messages' : messages,
      'username' : username,
      'title_qualify': "Public",
      'realm': "public",
      })
  return HttpResponse(t.render(c))


def public_river_sieve(request):
  latest_unread_pebbles = Reference.objects.filter(is_public=True).order_by('pub_date')[:MAX_ITEMS_PER_PAGE]
  t = loader.get_template('wom_river/sieve.html_dt')
  if not latest_unread_pebbles:
    messages = ["No pebble yet !"]
  else:
    messages = []
  if request.user.is_authenticated():
    user = request.user
    username = request.user.username
    user_collection_url = "/u/%s/collection/" % username
  else:
    user = None
    username = None
    user_collection_url = ""
  c = Context({
      'latest_unread_pebbles': generate_reference_user_status(user,latest_unread_pebbles),
      'messages' : messages,
      'username' : username,
      'num_unread_pebbles': len(latest_unread_pebbles),
      'title_qualify': "Public",
      'realm': "public",
      'user_collection_url': user_collection_url,
      })
  return HttpResponse(t.render(c))

def public_river_sources(request):
  t = loader.get_template('wom_river/river_sources.html_dt')
  sList = FeedSource.objects.filter(is_public=True).order_by('name')
  if not sList:
    messages = ["No source registered !"]
  else:
    messages = []
  if request.user.is_authenticated():
    username = request.user.username
  else:
    username = None
  c = Context({
      'source_list': sList,
      'messages' : messages,
      'username' : username,
      'title_qualify': "Public",
      'realm': "public",
      })
  return HttpResponse(t.render(c))

@login_required(login_url='/accounts/login/')
def user_river_view(request):
  user_profile = request.user.userprofile
  latest_items = []
  for source in user_profile.feed_sources.all():
    latest_items.extend(source.reference_set.order_by('-pub_date')[:MAX_ITEMS_PER_PAGE])
  latest_items.sort(key=lambda x:x.pub_date)
  latest_items.reverse()
  t = loader.get_template('wom_river/river.html_dt')
  if not latest_items:
    messages = ["No pebble yet !"]
  else:
    messages = []
  c = Context({
      'latest_unread_pebbles': latest_items[:MAX_ITEMS_PER_PAGE],
      'messages' : messages,
      'username' : request.user.username,
      'title_qualify': "Your",
      'realm': "u/%s" % request.user.username,
      })
  return HttpResponse(t.render(c))


def generate_user_sieve(request):
  """
  Generate the HTML page on which a given user will be able to see and
  use it's sieve to read and sort out the latests news.
  """
  check_user_unread_feed_items(request.user)
  latest_unread_pebbles = ReferenceUserStatus.objects.filter(has_been_read=False).select_related("ref","source").order_by('ref_pub_date')[:MAX_ITEMS_PER_PAGE]
  t = loader.get_template('wom_river/sieve.html_dt')
  if not latest_unread_pebbles:
    messages = ["No pebble yet !"]
  else:
    messages = []
  c = Context({
      'latest_unread_pebbles': latest_unread_pebbles,
      'messages' : messages,
      'username' : request.user.username,
      'num_unread_pebbles': len(latest_unread_pebbles),
      'title_qualify': "Your",
      'realm': "u/%s" % request.user.username,
      'user_collection_url': "/u/%s/collection/" % request.user.username,
      })
  return HttpResponse(t.render(c))
  
def apply_to_user_sieve(request):
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
    for rust in ReferenceUserStatus.objects.filter(has_been_read=False).select_related("ref").all():
      if rust.ref.url == read_url:
        rust.has_been_read = True
        modified_rust.append(rust)
        break  
  with transaction.commit_on_success():
    for r in modified_rust:
      r.save()
  count = len(modified_rust)
  response_dict = {u"action": u"read", u"status": u"success", u"count": count}
  return HttpResponse(simplejson.dumps(response_dict), mimetype='application/json')

@login_required(login_url='/accounts/login/')
def user_river_sieve(request):
  if request.method == 'GET':
    return generate_user_sieve(request)
  elif request.method == 'POST':
    return apply_to_user_sieve(request)
  else:
    return HttpResponseNotAllowed(['GET','POST'])
  
@login_required(login_url='/accounts/login/')
def user_river_sources(request):
  user_profile = request.user.userprofile
  t = loader.get_template('wom_river/river_sources.html_dt')
  sList = user_profile.feed_sources.all().order_by('name')
  if not sList:
    messages = ["No source registered !"]
  else:
    messages = []
  c = Context({
      'source_list': sList,
      'messages' : messages,
      'username' : request.user.username,
      'title_qualify': "Your",
      'realm': "u/%s" % request.user.username,
      })
  return HttpResponse(t.render(c))
