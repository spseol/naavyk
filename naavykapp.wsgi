# Change working directory so relative paths (and template lookup) work again
import os
import sys

dir = os.path.dirname(__file__) or '.'
sys.path.insert(0, dir + '/.venv/lib/python3.7/site-packages/' )
sys.path.insert(0, dir)

# print(sys.path)
from webface import app as application

# vim: ft=python
