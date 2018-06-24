#!/usr/bin/env python
import os
import shutil
from termcolor import colored

# We don't even load the app if this check fails
if not os.environ['VIRTUAL_ENV']:
    print('Activate the virtual environment first')
    exit(1)


# Instead of using yet another dependency like `bower-installer`, we'll just
# copy the static files we care about manually here.
root_dir = 'bower_components'
files = [
    # ['foundation.css', os.path.join(root_dir, 'foundation-sites', 'dist', 'css', 'foundation.css')],
    # ['foundation.min.css', os.path.join(root_dir, 'foundation-sites', 'dist', 'css', 'foundation.min.css')],
    # ['foundation.js', os.path.join(root_dir, 'foundation-sites', 'dist', 'js', 'foundation.js')],
    # ['foundation.min.js', os.path.join(root_dir, 'foundation-sites', 'dist', 'js', 'foundation.min.js')],
    # ['jquery.js', os.path.join(root_dir, 'jquery', 'dist', 'jquery.js')],
    # ['jquery.min.js', os.path.join(root_dir, 'jquery', 'dist', 'jquery.min.js')],
    # ['jquery.min.map', os.path.join(root_dir, 'jquery', 'dist', 'jquery.min.map')],
    # ['what-input.js', os.path.join(root_dir, 'what-input', 'dist', 'what-input.js')],
    # ['what-input.min.js', os.path.join(root_dir, 'what-input', 'dist', 'what-input.min.js')],
]
static_dist_dir = os.path.join('crypto_tracker', 'static', 'dist')
print('Updating static files in {}...'.format(static_dist_dir))
for file in files:
    src = os.path.abspath(file[1])
    if os.path.isfile(src):
        dst = os.path.abspath(os.path.join(static_dist_dir, file[0]))
        if os.path.isfile(dst) and (os.path.getmtime(dst) >= os.path.getmtime(src)):
            print(' * File {} is up-to-date'.format(file[0]))
        else:
            shutil.copy(src, dst)
            print(colored(' * Copied {} from source'.format(file[0]), 'green'))
    else:
        print(colored(' * File {} is missing from source'.format(file[0]), 'red'))
print()

from crypto_tracker import app  # noqa, E402
app.run(host=app.config['HOST'], port=app.config['PORT'])
