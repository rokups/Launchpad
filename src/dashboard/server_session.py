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
import marshal
import importlib.util
from contextlib import suppress

from django.db import transaction
from django.utils import timezone

from common.session import LaunchpadSession
from dashboard.models import Client


class LaunchpadServer(object):
    def __init__(self, session):
        self._session = session

    def greet(self):
        return 'Howdy'

    def import_module(self, module_name):
        try:
            spec = importlib.util.find_spec(module_name)
            if not spec:
                return None
            with open(spec.origin, 'rb') as fp:
                return marshal.dumps(compile(fp.read(), '<frozen>', 'exec'))
        except FileNotFoundError:
            return None


class LaunchpadServerSession(LaunchpadSession):
    def __init__(self, client_id):
        self.client_id = client_id
        super().__init__(LaunchpadServer(self), 'LaunchpadClient')

    def on_connect(self, connection):
        try:
            with transaction.atomic():
                client = Client.objects.get(client_id=self.client_id)
                client.date_connected = timezone.now()
                client.save()
        except Client.DoesNotExist as e:
            raise ConnectionError() from e
        else:
            super().on_connect(connection)

    def on_disconnect(self):
        super().on_disconnect()
        with suppress(Client.DoesNotExist):
            with transaction.atomic():
                client = Client.objects.get(client_id=self.client_id)
                client.date_disconnected = timezone.now()
                client.save()
