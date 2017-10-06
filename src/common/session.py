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
import logging

from goroutine import goroutine, yield_from
import tinyrpc


class SessionRpcManager(tinyrpc.RpcManager):
    def __init__(self, session):
        super().__init__()
        self._session = session

    def send(self, message):
        self._session.send(message)
        return yield_from(self._session.recv(message['id']))


class LaunchpadSession(object):
    clients = {}

    def __init__(self):
        self.connection = None
        self._dispatcher = SessionRpcManager(self)
        self._rpc_responses = {}
        self._rpc_wait_list = []

    def __getattr__(self, item_name):
        if item_name in self.__dict__:
            return self.__dict__[item_name]
        else:
            return self._dispatcher.get_object(item_name)

    def on_connect(self, connection):
        self.connection = connection

    def on_recv(self, msg: dict):
        """
        Handle message from remote host.
        :param msg: message from remote host.
        :return: True if message was unhandled.
        """
        if 'method' in msg:
            # rpc request, handle it.
            self.send(self._dispatcher.handle(msg))
        elif 'result' in msg or 'error' in msg:
            # rpc result, queue it for processing.
            msg_id = msg['id']
            if msg_id in self._rpc_wait_list:
                self._rpc_wait_list.remove(msg_id)
                if msg_id in self._rpc_responses:
                    raise ValueError(f'rpc message with id {msg_id} is already in the queue.')
                self._rpc_responses[msg_id] = msg
            else:
                logging.warning(f'Received rpc response with unknown id {msg_id}. Message discarded.')
        else:
            raise ValueError()

    def on_disconnect(self):
        self.connection = None

    def send(self, msg):
        """
        Queue message for sending. Method does not wait until message is actually sent.
        :param msg: dict with message contents
        """
        self._rpc_wait_list.append(msg['id'])
        self.connection.send(msg)

    @goroutine
    def recv(self, rpc_id, timeout=None):
        """
        Receive a response to rpc message. This does wait until message comes in and then returns it.
        :param rpc_id:
        :param timeout:
        :return:
        """
        wait_start = time.monotonic()
        while rpc_id not in self._rpc_responses:
            yield_from(asyncio.sleep(0.1))
            if timeout is not None:
                timeout -= time.monotonic() - wait_start
                if timeout <= 0:
                    return None
                wait_start = time.monotonic()
        return self._rpc_responses[rpc_id]
