import sys, os

# GoDaddy cPanel Python path - kendi virtual env path'ini gir
INTERP = os.path.expanduser("~/virtualenv/omninexus/3.11/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
application = create_app()
