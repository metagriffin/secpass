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
import morph

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
def resolveVars(expr):
  # note: this implementation allows recursive expansion BUT at the expense
  #       of not being able to escape an expansion....
  # todo: it would be nice to support both escaping and recursive expansion
  #       (note that default shell expansion is NOT recursive)
  while True:
    expr2 = os.path.expandvars(expr)
    if expr2 == expr:
      return expr2
    expr = expr2

#------------------------------------------------------------------------------
def resolvePath(path, reldir=None):
  path = os.path.expanduser(path)
  path = resolveVars(path)
  # TODO: use os.path.relpath?...
  if reldir is not None and not path.startswith('/'):
    path = os.path.join(reldir, path)
  return path

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
  if morph.tobool(config.get('generator.hex', DEFAULT_GENERATOR_HEX)):
    seq = seq.encode('hex')[:glen]
  else:
    seq = base64.b64encode(seq, 'Fh')[:glen]
  return seq

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
