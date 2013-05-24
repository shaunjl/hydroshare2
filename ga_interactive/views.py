import os
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
import urllib2
import sh
import time
from django.views.decorators.csrf import csrf_exempt

def run_notebook(ipython_arguments):
    ipython_arguments.extend(['--ext', 'django_extensions.management.notebook_extension'])
    sh.ipython('notebook', *ipython_arguments, _bg=True)

def notebook_for_user(request, *args, **kwargs):
    """
    This should proxy or create an IPython notebook inside of Django, but instead it redirects to the IPython
    notebook URL, forcing a person to go to a different web application entirely.  This is not ideal, but it's the
    best we can do right now, as IPython Notebook is complicated enough to be difficult to proxy to (it uses websockets)
    """
    user = request.user
    notebook_settings = list(settings.IPYTHON_SETTINGS)
    user_directory = os.path.join(settings.IPYTHON_BASE, user.email)
    port = 8888+user.pk
    hostname = '127.0.0.1'
    target_url='http://{hostname}:{port}/'.format(hostname=hostname, port=port)

    if user.is_authenticated():
        notebook_settings.append('--NotebookManager.notebook_dir={user_path}'.format(user_path=user_directory))
        notebook_settings.append('--ipython-dir={user_path}/ipython'.format(user_path=user_directory))
        notebook_settings.append('--port={port}'.format(port=port)) # ensure a unique port for each user
        notebook_settings.append('--pylab=inline')
        notebook_settings.append('--no-browser')

    if not os.path.exists(user_directory):
        os.mkdir(user_directory)
        os.mkdir(os.path.join(user_directory, user.email))

    try:
        urllib2.urlopen(target_url).read()
    except:
        print "no notebook found. running a new one in a subshell"
        run_notebook(notebook_settings)

    starting = 5
    while starting:
        try:
            urllib2.urlopen(target_url).read()
        except:
            time.sleep(1)
            starting -= 1

    return HttpResponseRedirect(target_url)