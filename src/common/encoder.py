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


def encode(obj):
    """
    Converts objects of various types to cbor-compatible types.
    :param obj: object
    :return: new value on success, raises ValueError on failure.
    """

    if isinstance(obj, (dict, set, list, str, int, float)):
        return obj

    if isinstance(obj, os.stat_result):
        return {
            'st_mode': obj.st_mode,
            'st_ino': obj.st_ino,
            'st_dev': obj.st_dev,
            'st_nlink': obj.st_nlink,
            'st_uid': obj.st_uid,
            'st_gid': obj.st_gid,
            'st_size': obj.st_size,
            'st_atime': obj.st_atime,
            'st_mtime': obj.st_mtime,
            'st_ctime': obj.st_ctime,
        }

    raise ValueError('Unknown object type can not be encoded')
