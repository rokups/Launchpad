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
import os
import shlex
import subprocess

import tinyrpc


@tinyrpc.public
class ShellClientModule(object):
    @classmethod
    def setup(cls):
        pass

    @tinyrpc.public
    def run_shell_command(self, shell_command, current_dir):
        if os.name == 'nt' and current_dir == '/':
            current_dir = 'C:/'
        try:
            ps = subprocess.Popen(shlex.split(shell_command), cwd=current_dir, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            result, _ = ps.communicate()
            result = result.decode()
        except Exception as e:
            result = str(e)
        if not result.endswith('\n'):
            result += '\n'
        return result
