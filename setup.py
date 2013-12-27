#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/04/27
# copy: (C) Copyright 2013-EOT metagriffin -- see LICENSE.txt
#------------------------------------------------------------------------------
# This software is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
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
  # TODO: upgrade to 2.9.5.0?
  # TODO: break secpass-gui into separate package.
  'wxPython             >= 2.9.4.0',
  'ObjectListView       >= 1.2dev',
]

entrypoints = {
  'console_scripts': [
    'secpass            = secpass.cli:main',
    'secpass-gui        = secpass.gui:main',
  ],
}

classifiers = [
  'Development Status :: 4 - Beta',
  #'Development Status :: 5 - Production/Stable',
  'Environment :: Console',
  'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
  'Natural Language :: English',
  'Operating System :: OS Independent',
  'Programming Language :: Python',
  'Topic :: Utilities',
  # TODO
]

setup(
  name                  = 'secpass',
  version               = '0.1.1',
  description           = 'Secure Passwords',
  long_description      = README,
  classifiers           = classifiers,
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
  license               = 'GPLv3+',
  )

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
