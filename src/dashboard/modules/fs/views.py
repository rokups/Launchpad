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

import os
from django.conf import settings
from django.conf.urls import url
from django.contrib import messages
from django.views.generic import TemplateView

from dashboard.mixins import ClientOnlineRequiredMixin
from dashboard.models import Client


class FilesystemView(ClientOnlineRequiredMixin, TemplateView):
    """
    Browse file system of the client.
    """
    template_name = 'client/module/fs/directory_listing.html'

    @staticmethod
    def format_listing(directory_listing):
        # Workaround for cbor2 encoding stat_result as a list
        for entry, info in directory_listing.items():
            info['stat'] = os.stat_result(info['stat'])

        # Sorts by entry type, directories first.
        def sort_key(item):
            return ('d' if item[1]['is_dir'] else 'f') + item[0]

        return dict(sorted(directory_listing.items(), key=sort_key))

    def get(self, request, client_id):
        entry = Client.objects.get(client_id=client_id)
        current_path = request.POST.get('cd', request.session.get('cd', '/'))
        if not current_path.endswith('/'):
            current_path += '/'
        request.session['cd'] = current_path
        directory_listing = None
        if current_path:
            try:
                directory_listing = entry.client.fs.enumerate_directory(current_path)
                directory_listing = self.format_listing(directory_listing)
            except AttributeError as e:
                directory_listing = None
                messages.error(request, 'Error: client is not connected.')

        context = {
            'client': entry,
            'current_path': current_path,
            'directory_listing': directory_listing
        }
        return self.render_to_response(context)

    def post(self, request, client_id):
        return self.get(request, client_id)


class FilesystemTextView(ClientOnlineRequiredMixin, TemplateView):
    """
    View textual content of a file.
    """
    template_name = 'client/module/fs/view_text.html'

    def post(self, request, client_id):
        entry = Client.objects.get(client_id=client_id)
        file_path = request.POST.get('path')
        if file_path:
            text_content = entry.client.fs.get_file_content(file_path)
            try:
                text_content = text_content.decode('utf-8')
            except UnicodeDecodeError as e:
                text_content = str(e)
        else:
            text_content = None

        context = {
            'client': entry,
            'file_path': file_path,
            'text': text_content
        }
        return self.render_to_response(context)


urlpatterns = [
    url(rf'^client/{settings.CLIENT_ID_REGEX}/fs$', FilesystemView.as_view(), name='client_filesystem'),
    url(rf'^client/{settings.CLIENT_ID_REGEX}/fs/view$', FilesystemTextView.as_view(), name='client_filesystem_view'),
]
