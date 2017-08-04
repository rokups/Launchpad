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
import sys

from django.conf import settings
from django.http import HttpResponse, Http404

from dashboard.models import Client
from dashboard.platform.windows import create_bootloader_win


def view_loader(request, client_id):
    try:
        client = Client.objects.get(client_id=client_id)
    except Client.DoesNotExist:
        raise Http404()

    try:
        loader = client.get_loader()
    except ValueError as e:
        raise Http404(str(e))

    bootloader = create_bootloader_win(
        settings.BINARIES_DIR / f'{client.platform}-{client.cpu}-{sys.version_info.major}.{sys.version_info.minor}.zip',
        settings.BINARIES_DIR / f'{client.platform}-{client.cpu}.exe',
        [f'--{client.method}', client.get_url()] + ['-vv'] if settings.DEBUG else []
    )

    loader_code = loader.get_loader(bootloader)

    return HttpResponse(loader_code)
