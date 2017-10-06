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
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from dashboard.models import Client


class ClientOnlineRequiredMixin(AccessMixin):
    """
    Prevents page from loading if client is offline. URL must be loaded with named parameter `client_id`.
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            client_id = request.resolver_match.kwargs['client_id']
        except KeyError:
            raise HttpResponse(status=500)

        entry = Client.objects.get(client_id=client_id)
        if not entry.is_online():
            messages.error(request, 'Client is offline.')
            return redirect(reverse('client_info', args=(client_id,)))
        return super().dispatch(request, *args, **kwargs)
