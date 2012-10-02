from django.template import Context, loader
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext


@login_required(login_url='/accounts/login/')
def user_profile(request):
  t = loader.get_template('wom_user/profile.html')
  c = Context({
      'username': request.user.username,
      })
  return HttpResponse(t.render(c))

from django import forms
from wom_river.tasks import opml2db

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

