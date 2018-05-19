#/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import sys

from flask import Flask, jsonify, request

from .reaction import Reaction

try:
    user = os.environ['GITHUB_USER']
    password = os.environ['GITHUB_PASSWORD']
    posts_location = os.environ.get('POSTS_LOCATION', u'content/post/')
except KeyError:
    sys.stderr.write(u'you need to specify env var'
                     u'`GITHUB_USER` and `GITHUB_PASSWORD`')
    exit(0)

app = Flask(__name__)


@app.route('/')
def hello():
    """main page"""
    return jsonify({
        'data': 'hello world!',
        'status': 'ok'
    })


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """do everything cool"""
    if request.method == 'GET':
        return jsonify({
            'data': 'you shall not pass',
            'status': 'error'
        }), 405

    event = request.headers.get('X-GitHub-Event', None)
    # delivery = request.headers.get('X-GitHub-Delivery', None)
    # signature = request.headers.get('X-Hub-Signature', None)
    # user_agent = request.headers.get('User-Agent', None)
    try:
        payload = request.json
    except:
        payload = {}

    reaction = Reaction(user, password, posts_location)
    res = reaction.run(event, payload)
    if res['status'] == 'ok':
        return jsonify(res)
    else:
        return jsonify(res), 500
