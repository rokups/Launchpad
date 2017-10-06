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
import datetime
import stat

from django import template
from django.apps import apps
from crequest.middleware import CrequestMiddleware
from django.urls import reverse

register = template.Library()


@register.simple_tag
def app_config(app_label='dashboard'):
    return apps.get_app_config(app_label)


@register.simple_tag
def on_active(url_path, return_value='active'):
    request = CrequestMiddleware.get_request()
    if request.path.startswith(url_path):
        return return_value


@register.simple_tag
def get_urls(url_list_name):
    return app_config().links[url_list_name]


@register.filter
def from_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)


@register.filter
def file_mode_to_str(mode):
    return stat.filemode(mode)
