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
import asyncio
import json
import logging

import aiohttp
import cbor2
from aiohttp import web
from goroutine import goroutine, yield_from

from common import encoder
from .interface import Connection


class WebSocketConnection(Connection):
    supported_protocols = ['ws', 'wss']
    supported_methods = ['connect']

    def __init__(self, session):
        super().__init__(session)
        self._client_session = None

    async def connect(self, address):
        try:
            self._client_session = aiohttp.ClientSession()
            self._socket = await self._client_session.ws_connect(address)
            self.on_connect()
        except (aiohttp.ClientConnectorError, ConnectionError) as e:
            self._client_session.close()
            self._client_session = None
            raise ConnectionError() from e

    async def accept(self, request):
        try:
            connection = web.WebSocketResponse()
            await connection.prepare(request)
            self._socket = connection
            self.on_connect()
        except (aiohttp.ClientConnectorError, ConnectionError) as e:
            raise ConnectionError() from e

    async def listen(self, target):
        raise NotImplementedError()

    async def run(self):
        try:
            await asyncio.gather(self._native_recv(), self._native_send())
        except (asyncio.CancelledError, ConnectionError, aiohttp.ClientConnectorError, EOFError) as e:
            raise e
        except Exception as e:
            logging.exception(e)
        finally:
            self.on_disconnect()
            if self._client_session is not None:
                self._client_session.close()
                self._client_session = None

    async def _native_send(self):
        while True:
            if not self._outgoing.empty():
                msg = self._outgoing.get()
                logging.debug('<< ' + str(msg))

                if isinstance(msg, bytes):
                    await self._socket.send_bytes(msg)
                elif isinstance(msg, dict):
                    await self._socket.send_bytes(cbor2.dumps(msg, default=encoder.cbor2_encoder))
                elif isinstance(msg, str):
                    await self._socket.send_str(msg)
                else:
                    raise ValueError('Payload must be bytes|dict|str')
                self._outgoing.task_done()
            else:
                await asyncio.sleep(0.01)

    async def _native_recv(self):
        while True:
            try:
                msg = await self._socket.receive()
            except TypeError:
                return None
            except TimeoutError:
                return None

            if msg.type == aiohttp.WSMsgType.TEXT:
                msg = json.loads(msg.data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                msg = cbor2.loads(msg.data, tag_hook=encoder.cbor2_decoder)
            elif msg.type == aiohttp.WSMsgType.CLOSING:
                pass
            elif msg.type == aiohttp.WSMsgType.CLOSED or msg.type == aiohttp.WSMsgType.CLOSE:
                raise EOFError()
            elif msg.type == aiohttp.WSMsgType.ERROR:
                raise ConnectionError() from self._socket.exception()
            else:
                raise ValueError('Unhandled result type')

            logging.debug('>> ' + str(msg))
            # Greenlet is spawned here in order to not block main loop. Message handler may send messages and
            # wait for response. In order to get a response this loop must be spinning.
            fut = asyncio.get_event_loop().create_task(self.on_recv(msg))
            fut.add_done_callback(lambda f: f.exception())  # make sure exception is retrieved

    @classmethod
    @goroutine
    def connect_and_run(cls, address, session):
        connection = cls(session)
        try:
            yield_from(connection.connect(address))
        except ConnectionError:
            logging.info('Connection failed.')
            return False
        else:
            logging.info(f'Connected to {address}.')

        try:
            yield_from(connection.run())
        except (ConnectionError, EOFError):
            logging.info('Disconnected from server.')
        except Exception as e:
            logging.exception(e)
        finally:
            yield_from(connection.close())

        return True
