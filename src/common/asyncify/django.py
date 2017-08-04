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
# aiohttp application which drives django.
import sys
import greenlet

from aiohttp.web_exceptions import HTTPRequestEntityTooLarge
from aiohttp.web_response import Response
from aiohttp_wsgi.wsgi import ReadBuffer, _run_application
from goroutine import goroutine, yield_from

aiohttp_application = None


def asyncify(debug=False):
    """
    Patch django `runserver` command to run django wsi application through aiohttp. In order to do additional aiohttp
    application setup add `setup_aiohttp(application)` method to your `AppConfig` subclass.
    :param debug: value of `settings.DEBUG`.
    """
    import asyncio
    from aiohttp import web
    from aiohttp_wsgi import WSGIHandler

    class CoroletWSGIHandler(WSGIHandler):
        """Creates a greenlet for every http request."""
        @asyncio.coroutine
        def handle_request(self, request):
            # Check for body size overflow.
            if request.content_length is not None and request.content_length > self._max_request_body_size:
                raise HTTPRequestEntityTooLarge()
            # Buffer the body.
            body_buffer = ReadBuffer(self._inbuf_overflow, self._max_request_body_size, self._loop, self._executor)

            try:
                while True:
                    block = yield from request.content.readany()
                    if not block:
                        break
                    yield from body_buffer.write(block)
                # Seek the body.
                body, content_length = yield from body_buffer.get_body()
                # Get the environ.
                environ = self._get_environ(request, body, content_length)
                status, reason, headers, body = (yield from goroutine(_run_application)(self._application, environ))
                return Response(status=status, reason=reason, headers=headers, body=body)

            finally:
                yield from body_buffer.close()

    # sys.set_coroutine_wrapper(goroutine)

    # Patch runserver command to run on aiohttp.
    def server_run(addr, port, wsgi_handler, loop=None, stop=None, **options):
        global aiohttp_application

        # Set up new asyncio loop based on gevent.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Wrap django wsgi application for aiohttp.
        protocol_factory = CoroletWSGIHandler(wsgi_handler)
        aiohttp_application = web.Application(debug=debug)

        # Call AppConfig.setup_aiohttp(application) if it exists.
        from django.apps import apps
        for app_config in apps.app_configs.values():
            setup_aiohttp = getattr(app_config, 'setup_aiohttp', None)
            if setup_aiohttp:
                setup_aiohttp(aiohttp_application)

        # Pass all routes to django.
        aiohttp_application.router.add_route("*", "/{path_info:.*}", protocol_factory)

        # Run aiohttp webserver.
        web.run_app(aiohttp_application, host=addr, port=port, handle_signals=False)

    from django.core.management.commands import runserver
    runserver.run = server_run


def provide_app_server_ready():
    """
    Patch runserver command to call AppConfig.server_ready() if it exists. This callback is called only on process
    which serves requests. Reloader process will not have this method called.
    """
    from django.core.management.commands import runserver
    __command_inner_run = runserver.Command.inner_run

    def command_inner_run(*args, **kwargs):
        from django.apps import apps
        for app_config in apps.app_configs.values():
            server_ready = getattr(app_config, 'server_ready', None)
            if server_ready:
                server_ready()
        return __command_inner_run(*args, **kwargs)
    runserver.Command.inner_run = command_inner_run
