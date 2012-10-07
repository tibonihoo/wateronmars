from django.http import HttpResponseRedirect
from wom_river.tasks import collect_all_new_pebbles_sync

def home(request):
  return HttpResponseRedirect('/public/river')

def request_for_update(request):
  collect_all_new_pebbles_sync()
  return HttpResponseRedirect('/public/river')
