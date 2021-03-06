#/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import sys
from hashlib import sha1
import hmac

from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify, request

from .reaction import Reaction
from .logging_helpers import get_desired_handler


try:
    load_dotenv(find_dotenv())
    user = os.environ['GITHUB_USER']
    password = os.environ['GITHUB_PASSWORD']
    secret_key = os.environ.get('GITHUB_SECRET', None) # maybe not enabled
    posts_location = os.environ.get('POSTS_LOCATION', u'content/post/')
except KeyError:
    sys.stderr.write(u'you need to specify env var'
                     u'`GITHUB_USER` and `GITHUB_PASSWORD`')
    exit(0)

app = Flask(__name__)
app.logger.addHandler(get_desired_handler())


@app.route('/')
def hello():
    """main page"""
    app.logger.info('someone come to landing page')
    return jsonify({
        'data': 'hello world!',
        'status': 'ok'
    })


@app.errorhandler(404)
def page_not_found(err):
    """404 page"""
    app.logger.error('someone come to 404 page')
    return jsonify({
        'data': 'no where to go :-(',
        'status': 'error'
    }), 404


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """do everything cool"""
    if request.method == 'GET':
        app.logger.error('someone try to GET /webhook, not allowed')
        return jsonify({
            'data': 'you shall not pass',
            'status': 'error'
        }), 405

    event = request.headers.get('X-GitHub-Event', None)
    # delivery = request.headers.get('X-GitHub-Delivery', None)
    signature = request.headers.get('X-Hub-Signature', None)
    # user_agent = request.headers.get('User-Agent', None)

    if secret_key is not None and secret_key: # ignore meaningless empty secret
        # then we do some basic verification
        bad_request = jsonify({
            'status': 'error',
            'data': 'invalid request'
        }), 400
        if signature is None:
            app.logger.error('we have a secret_key but request do not has signature')
            return bad_request
        signature = signature[len('sha1='):]
        try:
            secret_key_bytes = secret_key.encode('utf-8')
        except AttributeError:
            secret_key_bytes = secret_key
        computed = hmac.new(secret_key_bytes, request.data, sha1).hexdigest()
        signature_not_right = False
        if sys.version_info >= (2, 7, 7):
            if not hmac.compare_digest(str(signature), str(computed)):
                signature_not_right = True
        else:
            # old python version
            if str(signature) != str(computed):
                signature_not_right = True
        if signature_not_right:
            app.logger.error('wrong signature')
            return bad_request

    try:
        payload = request.json
    except:
        app.logger.error('paylog cannot be parsed?? interrupt.')
        return bad_request

    reaction = Reaction(user, password, app.logger, posts_location)
    res = reaction.run(event, payload)
    if res['status'] == 'ok':
        app.logger.info('everything is fine, return response')
        return jsonify(res)
    else:
        app.logger.info('something goes wrong, return 500 response')
        return jsonify(res), 500
