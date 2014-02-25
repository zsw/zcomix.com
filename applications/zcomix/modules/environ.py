#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
environ.py

Classes related to the environment.
"""

import os


class ServerEnvironmentError(Exception):
    """Exception class for when environment is not set properly."""
    pass


def has_terminal():
    """Return True if the script is run in a terminal environment

    The environment variables USER and TERM are checked.
        USER        TERM            has_terminal
        root        anything        True
        root        not defined     False
        http        anything        False

    The check can be overriden by setting the HAS_TERMINAL environment
    variable either to 'True' or 'False'
    """

    if 'HAS_TERMINAL' in os.environ:
        if os.environ['HAS_TERMINAL'] == 'False':
            return False
        if os.environ['HAS_TERMINAL'] == 'True':
            return True

    if 'USER' not in os.environ or not os.environ['USER']:
        return False
    if os.environ['USER'] != 'http' and 'TERM' in os.environ:
        return True
    return False


def server_production_mode(request):
    """Determine the production mode the server is in.

    Args:
        request: gluon.globals.Request instance
    Returns
        str: 'test' or 'live'
    """
    # If http_host = '127.0.0.1:8000' then web2py started from the shell.
    if request.env.http_host and request.env.http_host != '127.0.0.1:8000':
        server_mode = request.env.server_production_mode
        if not server_mode:
            raise ServerEnvironmentError("\n".join((
                    'request.env.server_production_mode variable not set.',
                    'Use SetEnv in httpd conf file.'
                )))
    else:
        server_mode = os.environ.get('SERVER_PRODUCTION_MODE', '')
        if not server_mode:
            raise ServerEnvironmentError("\n".join((
                    'SERVER_PRODUCTION_MODE environment variable not set.',
                    'Make sure local_rc file is sourced.'
                )))
    return server_mode
