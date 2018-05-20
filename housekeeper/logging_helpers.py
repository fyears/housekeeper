#/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import logging
from logging.handlers import RotatingFileHandler
import os

from dotenv import load_dotenv, find_dotenv
from flask import request

__all__ = ['get_desired_handler']


class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.url = request.url
        record.remote_addr = request.remote_addr
        record.event = request.headers.get('X-GitHub-Event', '<no event>')
        record.delivery = request.headers.get('X-GitHub-Delivery', '<no delivery>')
        record.signature = request.headers.get('X-Hub-Signature', '<no signature>')
        return super().format(record)

def get_desired_handler():
    """get the predifined logger handler"""
    # find the logging file?
    load_dotenv(find_dotenv())

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_log_dir = os.path.join(parent_dir, 'access_and_errors.log')
    log_dir = os.environ.get('LOG_DIR', default_log_dir)

    default_max_bytes = 10000
    max_bytes = int(os.environ.get('LOG_MAX_BYTES', default_max_bytes))

    default_backup_count = 10
    backup_count = int(os.environ.get('LOG_BACKUP_COUNT', default_backup_count))

    rotating_file_handler = RotatingFileHandler(
        log_dir, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')

    rotating_file_handler.setLevel(logging.INFO)

    request_formatter = RequestFormatter(
        u'[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        u'event: %(event)s\ndelivery: %(delivery)s\nsignature: %(signature)s\n'
        u'%(levelname)s in %(module)s: %(message)s'
    )
    rotating_file_handler.setFormatter(request_formatter)

    return rotating_file_handler
