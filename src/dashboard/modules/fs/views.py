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
import stat
import datetime

from django.conf import settings
from django.conf.urls import url
from django.contrib import messages
from django.views.generic import TemplateView

from dashboard.models import Client


class FilesystemView(TemplateView):
    template_name = 'client/module/filesystem.html'

    @staticmethod
    def format_listing(directory_listing):
        for entry, stats in directory_listing.items():
            stats['st_mode'] = stat.filemode(stats['st_mode'])
            stats['st_ctime'] = datetime.datetime.fromtimestamp(stats['st_ctime'])
            stats['st_mtime'] = datetime.datetime.fromtimestamp(stats['st_mtime'])
        return directory_listing

    def get(self, request, client_id):
        client = Client.objects.get(client_id=client_id)

        target_path = request.POST.get('d', '')
        directory_listing = None
        if target_path:
            try:
                directory_listing = client.session.fs_enumerate_directory(target_path)
                directory_listing = self.format_listing(directory_listing)
            except AttributeError:
                directory_listing = None
                messages.error(request, 'Error: client is not connected.')

        context = {
            'client': client,
            'directory_listing': directory_listing
        }
        return self.render_to_response(context)

    def post(self, request, client_id):
        return self.get(request, client_id)


urlpatterns = [
    url(rf'^client/{settings.CLIENT_ID_REGEX}/fs$', FilesystemView.as_view(), name='client_filesystem'),
]
