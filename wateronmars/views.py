from wom_user.views import add_base_template_context_data
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseNotAllowed


def home(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])
  d = add_base_template_context_data({},
                                     request.user.username,
                                     request.user.username)
  return render_to_response('wateronmars/home.html',d,
                            context_instance=RequestContext(request))

