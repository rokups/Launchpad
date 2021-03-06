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
import logging
from aiohttp.web import Application
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = 'dashboard'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.links = {
            'sidebar': [
               ('client_list', 'Clients'),
               ('client_add', 'Add Client'),
            ],
            'client': [
            ]
        }

    def ready(self):
        self.links['client'].append(['client_info', 'Info'])
        # TODO: gather these automatically
        self.links['client'].append(['client_filesystem', 'Filesystem'])
        self.links['client'].append(['client_shell', 'Shell'])

    def setup_aiohttp(self, application: Application):
        from dashboard.transport.ws import view_transport_ws
        logging.basicConfig(level=logging.DEBUG)
        application.router.add_get('/w/{client_id}', view_transport_ws)

    def __str__(self):
        return 'Workie'
