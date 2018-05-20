#/usr/bin/env python
# -*- coding: utf-8 -*-

"""
this is an example runner / wsgi file, useful especially for apache/mod_wsgi
kind of anti-pattern
you need to adapt the global variables below to make it work.
"""
from __future__ import unicode_literals, print_function
import os
import sys
import logging

VIRTUALENV_PATH = '/opt/py-virtualenv'
CONFIG_ENV_PATH = ''

this_dir = os.path.dirname(os.path.abspath(__file__))

# firstly we need to activate the virtualenv
activate_this = os.path.join(VIRTUALENV_PATH, 'bin', 'activate_this.py')
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# secondly we need to load some configurations
# import dotenv **after** ativating virtualenv!!
from dotenv import load_dotenv, find_dotenv
if CONFIG_ENV_PATH:
    config_env_path = CONFIG_ENV_PATH
else:
    config_env_path = os.path.join(this_dir, '.env')
# print('config_env_path: {}'.format(config_env_path))
load_dotenv(config_env_path)

# now we want to have the wsgi entry
# **after** loading some configurations
sys.path.insert(0, this_dir)
from housekeeper import app as application

# finally some other adjustments
# in production, flask logger is at the level logging.ERROR by default
application.logger.setLevel(logging.INFO) # pylint: disable=no-member
