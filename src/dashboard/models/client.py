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
import random
import re
import string

from django.db import models
from crequest.middleware import CrequestMiddleware

from common.session import LaunchpadSession
from common.transport import all_transports

from dashboard.modules import loaders


def _make_client_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=4))


class Client(models.Model):
    client_id = models.CharField(max_length=4, editable=False, unique=True, db_index=True, default=_make_client_id)
    title = models.CharField(max_length=128, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_connected = models.DateTimeField(null=True)
    date_disconnected = models.DateTimeField(null=True)
    platform = models.CharField(max_length=8, choices=[
        ('windows', 'Windows'),
    ])
    cpu = models.CharField(max_length=8, choices=[
        ('x86', 'x86'),
        ('x64', 'x64'),
    ])
    loader = models.CharField(max_length=8, choices=[(k, k) for k in loaders.all_loaders])
    protocol = models.CharField(max_length=8, choices=[(p, p) for t in all_transports for p in t.supported_protocols])
    method = models.CharField(max_length=8, choices=[
        ('connect', 'Connect'),
        ('bind', 'Bind'),           # TODO: implement this.
    ])

    def get_loader(self):
        try:
            return loaders.all_loaders[self.loader]()
        except KeyError:
            raise ValueError(f'Loader {self.loader} does not exist.')

    def get_url(self):
        request = CrequestMiddleware.get_request()
        if self.protocol in ('ws', 'wss'):
            url = request.build_absolute_uri(f'/w/{self.client_id}')
            url = re.sub(r'^https?://', f'{self.protocol}://', url)
        else:
            raise ValueError(f'Unsupported protocol {self.protocol}')
        return url

    @property
    def session(self):
        try:
            return LaunchpadSession.clients[self.client_id]
        except KeyError:
            return None

    @property
    def client(self):
        return self.session.client
