# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/01/09
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
import sys
import argparse
import asset
import morph
import logging

from .. import api, engine
from ..util import resolvePath, _

#------------------------------------------------------------------------------
class ProgramExit(Exception): pass

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
# command aliasing, shamelessly scrubbed from:
#   https://gist.github.com/sampsyo/471779
# TODO: make aliases not show up in command list...
# todo: in conjunction with aliases, use 'only-match' selection system...
#       ==> i.e. alias 'rotate' to 'set' and only-match 'rot' and 's'...
class AliasedSubParsersAction(argparse._SubParsersAction):
  class _AliasedPseudoAction(argparse.Action):
    def __init__(self, name, aliases, help):
      dest = name
      if aliases:
        dest += ' (%s)' % ','.join(aliases)
      sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
      sup.__init__(option_strings=[], dest=dest, help=help)
  def add_parser(self, name, **kwargs):
    if 'aliases' in kwargs:
      aliases = kwargs['aliases']
      del kwargs['aliases']
    else:
      aliases = []
    parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)
    # Make the aliases work.
    for alias in aliases:
      self._name_parser_map[alias] = parser
    # Make the help text reflect them, first removing old help entry.
    if 'help' in kwargs:
      help = kwargs.pop('help')
      self._choices_actions.pop()
      pseudo_action = self._AliasedPseudoAction(name, aliases, help)
      self._choices_actions.append(pseudo_action)
    return parser

#------------------------------------------------------------------------------
def ask(prompt):
  try:
    return raw_input(prompt).strip().lower()
  except EOFError:
    print '^D'
    raise ProgramExit(20)
  except KeyboardInterrupt:
    print '^C'
    raise ProgramExit(21)

#------------------------------------------------------------------------------
def confirm(prompt, exit=True):
  choice = ask(prompt)
  if not morph.tobool(choice):
    if exit:
      print _('Operation aborted.')
      raise ProgramExit(22)
    return False
  return True

#------------------------------------------------------------------------------
def makeCommonOptions(default_config=None, default_profile=None):

  if default_config is None:
    default_config = os.environ.get('SECPASS_CONFIG', api.DEFAULT_CONFIG)

  if default_profile is None:
    default_profile = os.environ.get('SECPASS_PROFILE', None)

  common = argparse.ArgumentParser(add_help=False)

  common.add_argument(
    _('-v'), _('--verbose'),
    dest='verbose', action='count', default=0,
    help=_('increase verbosity (can be specified multiple times)'))

  common.add_argument(
    _('-c'), _('--config'), metavar=_('FILENAME'),
    dest='config', default=default_config,
    help=_('configuration filename (current default: "{}")', '%(default)s'))

  common.add_argument(
    _('-p'), _('--profile'), metavar=_('PROFILE'),
    dest='profile', default=default_profile or None,
    help=(
      _('configuration profile (current default: "{}")', '%(default)s')
      if default_profile else
      _('configuration profile (default defined in configuration)')))

  common.add_argument(
    _('-r'), _('--regex'),
    dest='regex', action='store_true',
    help=_('switch the default processing of any EXPR or GLOB parameter to'
           ' use regular expressions (the default is to use, respectively,'
           ' natural-language evaluation and cocoon-style glob matching)'))

  return common

#------------------------------------------------------------------------------
def run(cli, argv):

  from .config import cmd_config

  options = cli.parse_args(args=argv)

  rootlog = logging.getLogger()
  rootlog.setLevel(logging.WARNING)
  rootlog.addHandler(logging.StreamHandler())
  # TODO: add a logging formatter...
  # TODO: configure logging from config.ini?...
  if options.verbose == 1:
    rootlog.setLevel(logging.INFO)
  elif options.verbose > 1:
    rootlog.setLevel(logging.DEBUG)

  options.config = resolvePath(options.config)

  if not os.path.isfile(options.config):
    if options.call is not cmd_config:
      cli.error(
        _('configuration "{}" does not exist -- use "{prog} config" to create it',
          options.config, prog=cli.prog))
    return options.call(options)
  if options.call is cmd_config:
    return options.call(options)

  try:
    options.engine = engine.Engine(options.config)
  except engine.ConfigError as e:
    cli.error(e)

  try:
    options.profile = options.engine.getProfile(options.profile)
  except KeyError:
    cli.error(_('profile "{}" not found', options.profile))

  try:
    # TODO: ==> in multi-query/glob mode, allow per-query/glob regex control...
    if getattr(options, 'query', False):
      options.query = ( 'regex:' if options.regex else 'query:') \
        + options.query
    # todo: if secnote, check that secure notes are supported by the active vault...
    if getattr(options, 'glob', False):
      options.glob = ( 'regex:' if options.regex else 'glob:') \
        + options.glob
    return options.call(options, options.profile)
  except ProgramExit as err:
    return err.message
  except api.Error as err:
    log.debug(
      'failed during execution of %s:', options.call.__name__, exc_info=True)
    print >>sys.stderr, '[**] ERROR: {}: {}'.format(
      err.__class__.__name__, err.message)
    return 100


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
