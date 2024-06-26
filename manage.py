#!/usr/bin/env python
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

import os
import sys



def quickloaddata(dumpfile):
    """Shortcut to init the django apps even when not everything is
    working yet and load data from a json dump.
    """
    import django
    django.setup()
    print(f"Starting loaddata from {dumpfile}")
    from django.db import transaction
    from django.core.management import call_command

    with transaction.atomic():
        call_command('loaddata', dumpfile, exclude=["contenttypes", "auth.permission"])


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wateronmars.settings")

    if "test" in sys.argv[1:]:
        # Make sure we're not in demo mode for the tests
        from django.conf import settings
        settings.DEMO=False
    elif "quickloaddata" in sys.argv[1:]:
        quickloaddata(sys.argv[2])

    from django.core.management import execute_from_command_line    
    execute_from_command_line(sys.argv)
