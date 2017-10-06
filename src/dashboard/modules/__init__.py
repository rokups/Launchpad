#
# MIT License
#
# Copyright 2017 Launchpad project contributors (see COPYRIGHT.md)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
import importlib
import os

from launchpad import settings


def enumerate_modules():
    base_dir = settings.BASE_DIR / 'dashboard' / 'modules'
    for module_pkg in os.listdir(str(base_dir)):
        yield base_dir, module_pkg


def register_module_template_dirs():
    """
    Appends module template dirs to `settings.TEMPLATES[0]['DIRS']`.
    """
    for base_dir, module_pkg in enumerate_modules():
        templates_dir = base_dir / module_pkg / 'templates'
        if os.path.isdir(templates_dir):
            settings.TEMPLATES[0]['DIRS'].append(str(templates_dir))


def gather_module_urlpatterns():
    """
    Imports views module from each module and appends it's urlpatterns list to dashboard urlpatterns.
    """
    for base_dir, module_pkg in enumerate_modules():
        if os.path.exists(base_dir / module_pkg / 'views.py') or os.path.exists(base_dir / module_pkg / 'views'):
            yield getattr(importlib.import_module(f'dashboard.modules.{module_pkg}.views'), 'urlpatterns', [])
