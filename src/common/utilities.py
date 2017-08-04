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

import marshal


def enumerate_files(top_dir, extension_filter: list or str=None):
    if isinstance(extension_filter, str):
        extension_filter = [extension_filter]

    top_dir = str(top_dir)
    for root, dirs, files in os.walk(top_dir):
        for file_name in files:
            if extension_filter:
                _, extension = os.path.splitext(file_name)
                if extension not in extension_filter:
                    continue
            file_path = os.path.join(root, file_name)
            archive_path = file_path[len(top_dir)+1:]
            yield archive_path


def compile_file(file, filename=None):
    file_data = None
    if isinstance(file, (str, os.PathLike)):
        if filename is None:
            filename = str(file)
        with open(file, 'rb') as fp:
            file_data = fp.read()
    else:
        filename = '<frozen>'
        if hasattr(file, 'read'):
            file_data = file.read()

    if file_data is None:
        raise ValueError('`file` must be a path to existing python file or a file-like object.')

    return marshal.dumps(compile(file_data, filename, 'exec', optimize=2))
