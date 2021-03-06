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
from django.conf import settings
from django.conf.urls import url
import dashboard.views
from dashboard.modules import gather_module_urlpatterns

urlpatterns = [
    url(r'^$', dashboard.views.view_index, name='index'),
    url(rf'^l/{settings.CLIENT_ID_REGEX}$', dashboard.views.view_loader, name='client_loader'),
    url(r'^client$', dashboard.views.view_client_list, name='client_list'),
    url(r'^new/client$', dashboard.views.ViewClientAdd.as_view(), name='client_add'),
    url(rf'^client/{settings.CLIENT_ID_REGEX}/info$', dashboard.views.ClientInfo.as_view(), name='client_info'),
]

for new_urlpatterns in gather_module_urlpatterns():
    urlpatterns.extend(new_urlpatterns)
