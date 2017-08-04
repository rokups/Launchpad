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
import random
import asyncio
import logging

from jsonrpc.jsonrpc import JSONRPCRequest
from jsonrpc.jsonrpc2 import JSONRPC20Request
from jsonrpc import JSONRPCResponseManager, Dispatcher
from goroutine import goroutine, yield_from

# Patch json-rpc to accept already decoded request.
JSONRPCRequest.deserialize = lambda d: d
JSONRPC20Request.deserialize = lambda d: d


class _RPCMethod(object):
    def __init__(self, session, method):
        self._session = session
        self._method = method

    def __call__(self, *args, **kwargs):
        if len(args) and len(kwargs):
            raise ValueError('RPC call must not mix positional and keyword arguments.')

        message = {
            'jsonrpc': '2.0',
            'id': random.randint(0, sys.maxsize),
            'method': self._method,
            'params': args or kwargs
        }

        self._session.send(message)
        response = yield_from(self._session.recv(message['id']))

        if 'error' in response:
            raise ValueError(response['error'])
        if 'result' not in response or 'id' not in response:
            raise ValueError('Invalid RPC response.')
        if response['id'] != message['id']:
            raise ValueError('RPC response id does not match.')
        return response['result']


class LaunchpadSession(object):
    clients = {}

    def __init__(self, local: object, remote: str):
        """
        :param local: Local object that can be called by remote session.
        :param remote: Remote object name that local session can call.
        """
        self.connection = None
        self._local = local
        self._dispatcher = Dispatcher()
        self._dispatcher.add_object(self._local)
        self._rpc_responses = {}
        self._rpc_wait_list = []
        self._prefix = remote.lower()

    def __getattr__(self, method_name):
        if method_name in self.__dict__:
            return self.__dict__[method_name]
        else:
            return _RPCMethod(self, f'{self._prefix}.{method_name}')

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
            msg = JSONRPCResponseManager.handle_request(JSONRPCRequest.from_json(msg), self._dispatcher).data
            self.send(msg)
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
