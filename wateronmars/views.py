from django.http import HttpResponseRedirect
from wom_river.tasks import collect_all_new_references_sync
from wom_river.tasks import delete_old_references_sync



def home(request):
  return HttpResponseRedirect('/public/river')

def request_for_update(request):
  collect_all_new_references_sync()
  delete_old_references_sync()
  return HttpResponseRedirect('/public/river')


def request_for_cleanup(request):
  delete_old_references_sync()
  return HttpResponseRedirect('/public/river')
