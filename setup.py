#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/27
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import os, sys, re
from setuptools import setup, find_packages

# require python 2.7+
assert(sys.version_info[0] > 2
       or sys.version_info[0] == 2
       and sys.version_info[1] >= 7)

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

test_requires = [
  'nose                 >= 1.3.0',
  'coverage             >= 3.5.3',
  ]

requires = [
  'distribute           >= 0.6.24',
  'argparse             >= 1.2.1',
  'python-gnupg         >= 0.3.3',

  # TODO: how to require these only if secpass-gui is wanted?...
  # todo: if linux, require wxPython >= 2.9.4.1
  'wxPython             >= 2.9.4.0',
  'ObjectListView       >= 1.2',
  ]

entrypoints = {
  'console_scripts': [
    'secpass            = secpass.cli:main',
    'secpass-gui        = secpass.gui:main',
    ],
  }

setup(
  name                  = 'secpass',
  version               = '0.1.1',
  description           = 'Secure Passwords',
  long_description      = README,
  classifiers           = [
    'Development Status :: 4 - Beta',
    #'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'License :: Public Domain',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Utilities',
    # TODO
    ],
  author                = 'metagriffin',
  author_email          = 'mg.pypi@uberdev.org',
  url                   = 'http://github.com/metagriffin/secpass',
  keywords              = 'secure password manager',
  packages              = find_packages(),
  namespace_packages    = ['secpass', 'secpass.driver'],
  include_package_data  = True,
  zip_safe              = False,
  install_requires      = requires,
  tests_require         = test_requires,
  test_suite            = 'secpass',
  entry_points          = entrypoints,
  license               = 'MIT (http://opensource.org/licenses/MIT)',
  )

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
