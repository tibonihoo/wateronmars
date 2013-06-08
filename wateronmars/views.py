from django.http import HttpResponseRedirect
from wom_river.tasks import collect_all_new_pebbles_sync
from wom_river.tasks import delete_old_pebbles_sync

def fill_base_data(username,title_qualify,d):
  """Generate the context data needed for template that inherit from the base template.
  'username': the user name of the  visitor's !
  'title_qualify': the qualification of the page wrt the visitor (Your
  or Public for now).
  """
  # TODO distinguish usernames as page_owner and visitor
  d.update({
    'username' : username,
    'title_qualify': title_qualify,
    'realm': "u/%s" % username
    })
  return d


def home(request):
  return HttpResponseRedirect('/public/river')

def request_for_update(request):
  collect_all_new_pebbles_sync()
  delete_old_pebbles_sync()
  return HttpResponseRedirect('/public/river')


def request_for_cleanup(request):
  delete_old_pebbles_sync()
  return HttpResponseRedirect('/public/river')
