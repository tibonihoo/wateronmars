from django.template import Context, loader
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from wom_pebbles.models import Reference
from wom_river.models import FeedSource

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
  latest_unread_pebbles = Reference.objects.filter(is_public=True).order_by('-pub_date')[:MAX_ITEMS_PER_PAGE]
  t = loader.get_template('wom_river/sieve.html_dt')
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
      'num_unread_pebbles': len(latest_unread_pebbles),
      'realm': "public",
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

@login_required(login_url='/accounts/login/')
def user_river_sieve(request):
  user_profile = request.user.userprofile
  latest_unread_pebbles = []
  for source in user_profile.feed_sources.all():
    latest_unread_pebbles.extend(source.reference_set.order_by('-pub_date')[:MAX_ITEMS_PER_PAGE])
  latest_unread_pebbles.sort(key=lambda x:x.pub_date)
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
      })
  return HttpResponse(t.render(c))

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
