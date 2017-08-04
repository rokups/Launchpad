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
from queue import Queue
from goroutine import goroutine


class Connection(object):
    supported_protocols = []
    supported_methods = []

    def __init__(self, session=None):
        self.session = session
        self._socket = None
        self._outgoing = Queue()

    async def connect(self, address):
        raise NotImplementedError()

    async def accept(self, request):
        raise NotImplementedError()

    async def listen(self, target):
        raise NotImplementedError()

    async def run(self):
        raise NotImplementedError()

    def send(self, msg):
        self._outgoing.put(msg)

    async def close(self):
        result = self._socket
        if self._socket:
            await self._socket.close()
            self._socket = None
        return result

    def on_connect(self):
        self.session.on_connect(self)

    @goroutine
    def on_recv(self, msg):
        self.session.on_recv(msg)

    def on_disconnect(self):
        self.session.on_disconnect()
