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
import time
import asyncio
from contextlib import suppress

import tinyrpc

from client.importer import RemoteImporter
from client.modules.fs import FilesystemClientModule
from common.session import LaunchpadSession
from common import transport


@tinyrpc.public
class LaunchpadClientSession(LaunchpadSession):
    def __init__(self):
        super().__init__()
        self._remote_importer = RemoteImporter(self)
        # Register self as rpc server
        self._dispatcher.register_object('client', self)
        # Retrieve client to rpc server on the other end
        self.server = self._dispatcher.get_object('server')
        # Initialize plugins
        self.fs = FilesystemClientModule()

    def on_connect(self, connection):
        super().on_connect(connection)
        # sys.meta_path.insert(0, self._remote_importer)

    def on_disconnect(self):
        with suppress(ValueError):
            sys.meta_path.remove(self._remote_importer)
        super().on_disconnect()


def get_reconnect_sleep_time(retry: int, args):
    # Assumes reconnects are sorted from largest retry count to lowest.
    for retries, seconds in args.reconnect:
        if retry < retries:
            return seconds
    return args.reconnect_default


def run_connect(args):
    address = args.connect
    protocol, _ = args.connect.split('://', 1)

    for t in transport.all_transports:
        if protocol in t.supported_protocols and 'connect' in t.supported_methods:
            transport_factory = t
            break
    else:
        raise RuntimeError(f'No "connect" transport available for protocol {protocol}')

    session = LaunchpadClientSession()

    # TODO: better, configurable retry system, maybe move into transport?
    retry = 0
    loop = asyncio.get_event_loop()
    try:
        while True:
            start_time = time.monotonic()
            connected = loop.run_until_complete(transport_factory.connect_and_run(address, session))
            if (time.monotonic() - start_time) < 5:
                # If connection did not last for 5 seconds consider it as failed.
                connected = False
            if connected:
                retry = 0
            else:
                retry += 1
                sleep_time = get_reconnect_sleep_time(retry, args)
                if sleep_time is None:
                    break
                else:
                    time.sleep(sleep_time)
    finally:
        loop.close()
