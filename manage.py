#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wateronmars.settings")

    if "runserver" in sys.argv[1:]:
        # Use Eldarion/Pinax's trick to get an entry point at startup
        # (see http://eldarion.com/blog/2013/02/14/entry-point-hook-django-projects/)
        import wateronmars.startup as startup
        startup.run()
    if "test" in sys.argv[1:]:
        # Make sure we're not in demo mode for the tests
        from django.conf import settings
        settings.DEMO=False
        
    from django.core.management import execute_from_command_line    
    execute_from_command_line(sys.argv)
