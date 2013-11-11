from django.http import HttpResponseRedirect
from wom_river.tasks import collect_all_new_references_sync
from wom_river.tasks import delete_old_references_sync

class WOMPublic(object):
  
  def __init__(self):
    self.username = ''

WOMPublic = WOMPublic()

def wom_add_base_context_data(d,visitor_name, owner_name):
  """Generate the context data needed for templates that inherit from
  the base template.
  
  'd': the dictionary of custom data for the context.
  'visitor_name': the username of the visitor ("None" if anonymous).
  'owner_name': the username of the owner (WOMPublic if public).
  """
  if visitor_name == owner_name:
    tq = "Your"
  elif owner_name is WOMPublic:
    tq = "Public"
  else:
    tq = "%s's" % owner_name
  if owner_name is WOMPublic:
    r = "public"
  else:
    r = "u/%s" % owner_name
  d.update({
      'visitor_name' : visitor_name,
      'owner_name' : owner_name,
      'title_qualify': tq,
      'realm': r
      })
  return d


def home(request):
  return HttpResponseRedirect('/public/river')

def request_for_update(request):
  collect_all_new_references_sync()
  delete_old_references_sync()
  return HttpResponseRedirect('/public/river')


def request_for_cleanup(request):
  delete_old_references_sync()
  return HttpResponseRedirect('/public/river')
