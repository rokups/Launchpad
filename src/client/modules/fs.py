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
from contextlib import suppress

import tinyrpc


@tinyrpc.public
class FilesystemClientModule(object):
    @classmethod
    def setup(cls):
        pass

    @tinyrpc.public
    def enumerate_directory(self, dir_path):
        # Default path is always /, handle it for different systems
        if os.name == 'nt' and dir_path == '/':
            dir_path = 'C:/'

        result = {}
        for filename in os.listdir(dir_path):
            full_path = os.path.join(dir_path, filename)
            file_info = {
                'stat': None,
                'is_dir': os.path.isdir(full_path),
                'is_link': os.path.islink(full_path),
                'is_mount': os.path.ismount(full_path),
                'is_file': os.path.isfile(full_path),
            }
            with suppress(OSError, KeyError):
                file_info['stat'] = os.stat(full_path)
            result[filename] = file_info
        return result

    @tinyrpc.public
    def get_file_content(self, file_path):
        return open(file_path, 'rb').read()
