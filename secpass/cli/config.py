# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/01/29
# copy: (C) Copyright 2014-EOT metagriffin -- see LICENSE.txt
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

import os
import asset

from ..util import _

DEFAULT_CONFIG_DATA = asset.load('secpass:res/config.ini').read()

#------------------------------------------------------------------------------
def addConfigCommand(commands, common):
  subcli = commands.add_parser(
    _('config'),
    parents=[common],
    help=_('create and/or manage secpass/secnote configuration file'))
  # subcli.add_argument(
  #   _('-f'), _('--force'),
  #   dest='force', action='store_true',
  #   help=_('force overwrite of existing configuration file'))
  subcli.set_defaults(call=cmd_config)

#------------------------------------------------------------------------------
def cmd_config(options):
  # USAGE: config [..TODO...]

  print 'TODO:COMMAND.CONFIG'

  # if os.path.exists(options.config):
  #   if not options.force:
  #     print >>sys.stderr, _('file "{}" exists -- use "--force" to overwrite',
  #                           options.config)
  #     return 20

  # cdir = os.path.dirname(options.config)
  # if not os.path.isdir(cdir):
  #   os.makedirs(cdir)
  # with open(options.config, 'wb') as fp:
  #   fp.write(DEFAULT_CONFIG_DATA)
  # return 0

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
