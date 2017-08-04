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
from contextlib import suppress

from aiohttp import web

from common.session import LaunchpadSession
from common.transport import WebSocketConnection
from dashboard.server_session import LaunchpadServerSession


async def view_transport_ws(request):
    client_id = request.match_info.get('client_id')
    if not client_id:
        raise web.RequestPayloadError()

    session = LaunchpadServerSession(client_id)
    connection = WebSocketConnection(session)

    try:
        await connection.accept(request)
        LaunchpadSession.clients[client_id] = session
        await connection.run()
    except EOFError:
        pass
    except Exception as e:
        raise web.HTTPInternalServerError() from e
    finally:
        logging.info(f'Client {client_id} disconnected.')
        with suppress(KeyError):
            del LaunchpadSession.clients[client_id]
        return await connection.close()
