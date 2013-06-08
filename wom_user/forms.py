from django import forms
from django.contrib.auth.forms import UserCreationForm

from wom_user.models import UserProfile

class OPMLFileUploadForm(forms.Form):
  """From used to upload an OPML file."""
  opml_file  = forms.FileField("OPML file")

class UserProfileCreationForm(UserCreationForm):
  """Customized form to require an email and create a profile at the same time as creating a user."""

  email = forms.EmailField(required=True)
  
  def save(self, commit=True):
    """
    Warning: the User instance will be saved whether commit is True or False.
    Returns a UserProfile instance (not saved if commit==False).
    """
    user = super(UserProfileCreationForm, self).save(commit=False)
    user.email = self.cleaned_data["email"]
    user.save()
    profile = UserProfile()
    profile.user = user
    if commit:
      profile.save()
    return profile
