#!/usr/bin/env python3
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


def main():
    import os
    import sys
    import logging
    import argparse
    from contextlib import suppress

    if not getattr(sys, 'frozen', False):
        # Append parent directory to PYTHONPATH. Fixes the case where project is executed from command line.
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # else:
    #     for name in sys.builtin_module_names:
    #         if name.startswith('__native__'):
    #             real_module_name = name[10:].replace('__dot__', '.')
    #             sys.modules[real_module_name] = __import__(name)

    from client.client_session import run_connect

    parser = argparse.ArgumentParser()
    parser.add_argument('--connect', help='Address to connect to.', metavar='protocol://address[:port]', required=True)
    parser.add_argument('--reconnect', nargs=2, action='append', metavar=('TRIES', 'SECONDS'),
                        help='Customize reconnect behavior. Up to number of `TRIES` after failed connection attempt '
                             'client will sleep for specified number of `SECONDS`.')
    parser.add_argument('--reconnect-default', type=int, metavar='SECONDS',
                        help='Default reconnect time. If not specified application will exit after specified number of '
                             'retries.')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()

    default_verbosity_level = logging.WARNING
    logging.basicConfig(level=(default_verbosity_level - args.verbose * 10))

    if args.reconnect:
        args.reconnect = list(map(lambda p: list(map(int, p)), args.reconnect))
        args.reconnect = sorted(args.reconnect, key=lambda v: v[0], reverse=True)
    else:
        # Default reconnect policy.
        args.reconnect = [(3, 1), (6, 3)]

    with suppress(KeyboardInterrupt):
        if args.connect:
            run_connect(args)
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import logging
        logging.exception(e)
