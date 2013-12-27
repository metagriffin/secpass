# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/04/25
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

import os, re, time, random, base64, gettext
from .adict import adict
from .resolve import resolve
from .glob2re import glob2re

#------------------------------------------------------------------------------
DEFAULT_GENERATOR_MIN = 24
DEFAULT_GENERATOR_MAX = 32
DEFAULT_GENERATOR_HEX = False

#------------------------------------------------------------------------------
def _(msgid, *args, **kw):
  if args or kw:
    return gettext.gettext(msgid).format(*args, **kw)
  return gettext.gettext(msgid)

#------------------------------------------------------------------------------
def resolvePath(name, rel=None):

  # TODO: use:
  #  - os.path.expanduser
  #  - os.path.expandvars
  #  - os.path.relpath

  # todo: this is pretty simplistic...
  return name.replace('~', os.environ.get('HOME', ''))

#------------------------------------------------------------------------------
truthy = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))
def asbool(s):
  # shamelessly scrubbed from pyramid.settings:asbool
  if s is None:
    return False
  if isinstance(s, bool):
    return s
  s = str(s).strip()
  return s.lower() in truthy

#------------------------------------------------------------------------------
def zulu(ts=None, ms=True):
  '''
  Returns the specified epoch time (or current time if None or not
  provided) as an ISO 8601 string in zulu time (with millisecond
  precision), e.g. zulu(1362187446.553) => '2013-03-02T01:24:06.553Z'.
  If `ms` is True (the default), milliseconds will be included, otherwise
  truncated.
  '''
  if ts is None:
    ts = time.time()
  ms = '.%03dZ' % (ts * 1000 % 1000,) if ms else 'Z'
  return time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(ts)) + ms

#------------------------------------------------------------------------------
def localtime(ts=None, ms=True):
  if ts is None:
    ts = time.time()
  ms = '.%03d' % (ts * 1000 % 1000,) if ms else ''
  return time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(ts)) + ms

#------------------------------------------------------------------------------
def generatePassword(config):
  gmin = int(config.get('generator.min', DEFAULT_GENERATOR_MIN))
  gmax = int(config.get('generator.max', DEFAULT_GENERATOR_MAX))
  glen = random.randint(gmin, gmax)
  # note: this generates more data than necessary... oh well. if i am
  # *really* bored one day, it could be fixed...
  seq = ''
  for i in range(glen):
    seq += chr(random.randint(0, 255))
  if asbool(config.get('generator.hex', DEFAULT_GENERATOR_HEX)):
    seq = seq.encode('hex')[:glen]
  else:
    seq = base64.b64encode(seq, 'Fh')[:glen]
  return seq

#------------------------------------------------------------------------------
def pick(src, *keys):
  '''
  Given a dict and iterable of keys, return a dict containing
  only those keys.
  '''
  if not src: # pragma: no cover
    return dict()
  try:
    return {k: v for k, v in src.items() if k in keys}
  except AttributeError:
    return {k: getattr(src, k) for k in keys if hasattr(src, k)}

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
