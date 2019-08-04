# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2013-2019 Thibauld Nion
#
# This file is part of WaterOnMars (https://github.com/tibonihoo/wateronmars) 
#
# WaterOnMars is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# WaterOnMars is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with WaterOnMars.  If not, see <http://www.gnu.org/licenses/>.
#

from django.conf import settings
from django.apps import AppConfig
  
class WomUserConfig(AppConfig):
    name = 'wom_user'
    verbose_name = "WomUser"
    def ready(self):
        import os
        if os.environ.get('RUN_MAIN'):
            startup()

OPML_TXT = """\
<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
  <title>My Subcriptions</title>
  </head>
  <body>
  <outline title="News" text="News">
    <outline text="Richard Stallman's Political Notes"
         title="Richard Stallman's Political Notes" type="rss"
         xmlUrl="http://stallman.org/rss/rss.xml" htmlUrl="http://stallman.org/archives/polnotes.html"/>
    <outline text="Dave's LifeLiner" title="Dave's LifeLiner"
         type="rss" xmlUrl="http://www.scripting.com/rss.xml" htmlUrl="http://scripting.com/"/>
  </outline>
  <outline title="Culture" text="Culture">
    <outline text="Open Culture" title="Open Culture" type="rss"
         xmlUrl="http://www.openculture.com/feed" htmlUrl="http://www.openculture.com"/>
  </outline>
  </body>
</opml>
"""

NS_BOOKMARKS_TXT = """\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<!-- This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
<DT><A HREF="https://www.djangoproject.com/" PRIVATE="0" TAGS="technology,web">Django Project</A>
<DD>The Web framework for perfectionists with deadlines.
<DT><A HREF="http://getbootstrap.com/" PRIVATE="0" TAGS="technology,web">Twitter Bootstrap</A>
<DD>Sleek, intuitive, and powerful mobile first front-end framework for faster and easier web development.
<DT><A HREF="http://wikipedia.org" PRIVATE="0" TAGS="culture">Wikipedia</A>
<DD>The free encyclopedia that anyone can edit.
"""

NS_BOOKMARKS_TXT_MORE_TEMPLATE = """\
<DT><A HREF="http://example.org/%d" PRIVATE="1" TAGS="culture">Example %d</A>
<DD>An example tag to test the pagination.
"""


def startup():
  from django.contrib.auth.models import User
  from wom_user.models import UserProfile
   
  from wom_user.tasks import import_user_feedsources_from_opml
  from wom_user.tasks import import_user_bookmarks_from_ns_list

  print("DEMO mode: Ensuring demo user is available.")
  if settings.DEMO and not User.objects.filter(username=settings.DEMO_USER_NAME).exists():
    raise Warning("DEMO mode: Creating demo user.")
    demo_user = User(username=settings.DEMO_USER_NAME)
    demo_user.set_password(settings.DEMO_USER_PASSWD)
    demo_user.save()
    demo_profile = UserProfile.objects.create(owner=demo_user)
    demo_profile.save()
    print("DEMO mode: Importing default bookmarks and feeds for demo user.")
    import_user_bookmarks_from_ns_list(demo_user,
                                       NS_BOOKMARKS_TXT \
                                       + "".join(NS_BOOKMARKS_TXT_MORE_TEMPLATE \
                                                 % (i,i) for i in range(200)))
    import_user_feedsources_from_opml(demo_user,OPML_TXT)
    print("DEMO mode: demo user setup finished.")
            
