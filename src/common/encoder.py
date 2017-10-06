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
from enum import Enum

from cbor2 import CBORTag


class _Tags(Enum):
    EXCEPTION = 1000


def cbor2_encoder(encoder, value):
    """
    Converts objects of various types to cbor-compatible types.
    :param encoder: cbor encoder that should be called
    :param value: value to encode
    """

    if isinstance(value, Exception):
        encoder.encode(CBORTag(_Tags.EXCEPTION.value, encoder.encode_to_bytes({
            'type': type(value).__name__,
            'dict': value.__dict__
        })))
    else:
        raise ValueError('Encoding of type {} is not supported'.format(type(value).__name__))


def cbor2_decoder(decoder, tag, shareable_index=None):
    if tag.tag == _Tags:
        state = decoder.decode_from_bytes(tag.value)
        if tag.tag == _Tags.EXCEPTION.value:
            tag_type = __builtins__[state['type']]
        else:
            raise ValueError('Decoding of tag {} is not supported'.format(tag.tag))
        instance = tag_type.__new__(tag_type)
        decoder.set_shareable(shareable_index, instance)
        instance.__dict__.update(state)
        return instance
    else:
        return tag
