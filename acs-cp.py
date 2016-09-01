#!/usr/bin/env python

import bottle
from bottle import get, post, static_file, request, route, template
from bottle import SimpleTemplate
from configparser import ConfigParser
import os
from os import path
import ssl
from SOAPpy import SOAPProxy

@get('/')
def get_index():
    return index_tpl()


@post('/')
def post_index():
    form = request.forms.getunicode

    def error(msg):
        return index_tpl(username=form('username'), alerts=[('error', msg)])

    if form('new-password') != form('confirm-password'):
        return error("Password doesn't match the confirmation!")

    if len(form('new-password')) < 6:
        return error("Password must be at least 6 characters long!")

    try:
        change_password(form('username'), form('old-password'), form('new-password'))
    except Error as e:
        print("Unsuccessful attempt to change password for %s: %s" % (form('username'), e))
        return error(str(e))

    print("Password successfully changed for: %s" % form('username'))

    return index_tpl(alerts=[('success', "Password has been changed")])


@route('/static/<filename>', name='static')
def serve_static(filename):
    return static_file(filename, root=path.join(BASE_DIR, 'static'))

def change_password(*args):

    # Get the ACS host / IP
    host = CONF['acs']['host']
    targetUrl = 'https://' + host + '/PI/services/UCP/'

    server = SOAPProxy(targetUrl, 'UCP')

    # Call the changeUserPassword with given input
    try:
        ans = server.changeUserPass(args[0],args[1],args[2])
    except:
        raise Error('Problems connecting to:  %s' % host)
    else:
        # Password changing failed
        if ans.status == 'failure':
            raise Error('Username or Password is incorrect!')

            # Print all failure reasons
            for err in ans.errors:  
              raise Error(err)
        else:
            # Password was changed successfully
            return 'Success'


def index_tpl(**kwargs):
    return template('index', **kwargs)

def read_config():
    config = ConfigParser()
    config.read([path.join(BASE_DIR, 'settings.ini'), os.getenv('CONF_FILE', '')])

    return config


class Error(Exception):
    pass


BASE_DIR = path.dirname(__file__)
CONF = read_config()

bottle.TEMPLATE_PATH = [ BASE_DIR ]

# Set default attributes to pass into templates.
SimpleTemplate.defaults = dict(CONF['html'])
SimpleTemplate.defaults['url'] = bottle.url


# Run bottle internal server when invoked directly (mainly for development).
if __name__ == '__main__':
    bottle.run(**CONF['server'])
# Run bottle in application mode (in production under uWSGI server).
else:
    application = bottle.default_app()
