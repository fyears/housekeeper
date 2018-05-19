#/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse # type: ignore
import datetime


def extract_info_from_url(url):
    """read the url of the api"""
    parsed = urlparse(url)
    addr = parsed.netloc
    subdir = parsed.path
    info = subdir.split('/')
    res = {}
    if addr == 'github.com':
        if len(info) >= 2:
            # always /{owner}/{repo}/something
            res = {
                'owner': info[1],
                'repo': info[2]
            }
    elif addr == 'api.github.com':
        if len(info) >= 3:
            # always /{?}/{owner}/{repo}/{obj}/{number}
            res = {
                'owner': info[2],
                'repo': info[3]
            }
            if len(info) >= 5:
                res.update({
                    'number': int(info[5])
                })
    return res


def get_today():
    """today object"""
    return datetime.date.today()
