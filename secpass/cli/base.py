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
import re
import argparse
import asset
import morph
import logging
import formencode
from formencode import validators
import getpass
import blessings
import textwrap

from .. import api, engine
from ..util import resolvePath, _

#------------------------------------------------------------------------------
class ProgramExit(Exception): pass

log = logging.getLogger(__name__)

WARRANTY = '''\
This software is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This software is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see http://www.gnu.org/licenses/.
'''

#------------------------------------------------------------------------------
# command aliasing, shamelessly scrubbed from:
#   https://gist.github.com/sampsyo/471779
# (with some adjustments to make aliases only show up in non-summary help)
# todo: in conjunction with aliases, use 'only-match' selection system...
#       ==> i.e. alias 'rotate' to 'set' and only-match 'rot' and 's'...
class AliasedSubParsersAction(argparse._SubParsersAction):
  fuzzy = True
  class _AliasedPseudoAction(argparse.Action):
    def __init__(self, name, aliases, help):
      dest = name
      if aliases:
        dest += ' (%s)' % ','.join(aliases)
      sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
      sup.__init__(option_strings=[], dest=dest, help=help)
  def __init__(self, *args, **kw):
    super(AliasedSubParsersAction, self).__init__(*args, **kw)
    self.aliases = []
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
    self.aliases.extend(aliases)
    # Make the help text reflect them, first removing old help entry.
    if 'help' in kwargs:
      help = kwargs.pop('help')
      self._choices_actions.pop()
      pseudo_action = self._AliasedPseudoAction(name, aliases, help)
      self._choices_actions.append(pseudo_action)
    return parser

#------------------------------------------------------------------------------
class AliasSuppressingHelpFormatter(argparse.HelpFormatter):
  def _metavar_formatter(self, action, default_metavar):
    tmp = None
    if isinstance(action, AliasedSubParsersAction):
      tmp = action.choices
      action.choices = [ch for ch in tmp if ch not in action.aliases]
    ret = super(AliasSuppressingHelpFormatter, self)._metavar_formatter(action, default_metavar)
    if tmp is not None:
      action.choices = tmp
    return ret

#------------------------------------------------------------------------------
class WarrantyAction(argparse.Action):
  def __init__(self, option_strings, warranty=None,
               dest=argparse.SUPPRESS, default=argparse.SUPPRESS,
               help="show program's warranty and exit"):
    super(WarrantyAction, self).__init__(
      option_strings=option_strings,
      dest=dest, default=default, nargs=0, help=help)
    self.warranty = warranty
  def __call__(self, parser, namespace, values, option_string=None):
    parser.exit(message=self.warranty)

#------------------------------------------------------------------------------
class FuzzyChoiceArgumentParser(argparse.ArgumentParser):
  def __init__(self, *args, **kw):
    if 'formatter_class' not in kw:
      kw['formatter_class'] = AliasSuppressingHelpFormatter
    super(FuzzyChoiceArgumentParser, self).__init__(*args, **kw)
  def _fuzzy_get_value(self, action, value):
    maybe = [item for item in action.choices if item.startswith(value)]
    if len(maybe) == 1:
      return maybe[0]
    match = re.compile('^' + '.*'.join([re.escape(ch) for ch in value]))
    maybe = [item for item in action.choices if match.match(item)]
    if len(maybe) == 1:
      return maybe[0]
    return None
  def _get_value(self, action, arg_string):
    if getattr(action, 'fuzzy', False) \
        and getattr(action, 'choices', None) is not None \
        and arg_string not in action.choices:
      ret = self._fuzzy_get_value(action, arg_string)
      if ret is not None:
        return ret
    return super(FuzzyChoiceArgumentParser, self)._get_value(action, arg_string)

#------------------------------------------------------------------------------
def layout(rst, indent=None, block=False, width=None):
  # todo: use actual reStructuredText processing...
  if width is None:
    width = blessings.Terminal().width
  if block:
    indent = indent or '  '
  ret = '\n\n'.join([
    textwrap.fill(para, width=width,
                  initial_indent=indent or '',
                  subsequent_indent=indent or '')
    for para in rst.split('\n\n')])
  if block:
    ret = '\n' + ret + '\n'
  return ret + '\n'

#------------------------------------------------------------------------------
def out(msg='', newline=True):
  # using a proxy so that testing works
  # todo: move to use `stub` and this need should go away
  return _out(msg=msg, newline=newline)
def _out(msg='', newline=True):
  sys.stdout.write(msg)
  if newline:
    sys.stdout.write('\n')

#------------------------------------------------------------------------------
def ask(prompt, lower=True, strip=True, echo=True, validator=None, default=None):
  if prompt is not None:
    if default is None:
      prompt = layout(_('{prompt}:', prompt=prompt))
    else:
      prompt = layout(_('{prompt} [{default}]:', prompt=prompt, default=default))
    prompt = prompt.strip() + ' '
  while True:
    try:
      prompter = raw_input if echo else getpass.getpass
      if prompt:
        ret = prompter(prompt)
      else:
        ret = prompter()
      if ret == '' and default is not None:
        out()
        return default
      if validator is None:
        if strip:
          ret = ret.strip()
        if lower:
          ret = ret.lower()
        out()
        return ret
      ret = validator.to_python(ret)
      out()
      return ret
    except formencode.Invalid as err:
      # todo: i18n formencode...
      out(_('{error}... please try again.', error=str(err)))
    except EOFError:
      out(_('^D'))
      raise ProgramExit(20)
    except KeyboardInterrupt:
      out('' if echo else _('^C'))
      raise ProgramExit(21)

#------------------------------------------------------------------------------
def confirm(prompt, default=False):
  if default is True:
    prompt = _('{prompt} (Y/n)', prompt=prompt)
  elif default is False:
    prompt = _('{prompt} (y/N)', prompt=prompt)
  choice = ask(prompt)
  return morph.tobool(choice, default=default)

#------------------------------------------------------------------------------
def confirmOrExit(prompt, **kw):
  ret = confirm(prompt, **kw)
  if not ret:
    out(_('Operation aborted.'))
    raise ProgramExit(22)
  return True

#------------------------------------------------------------------------------
def pause(prompt=None):
  if prompt is None:
    prompt = _('Press enter to continue')
  return ask(prompt, validator=validators.String())

#------------------------------------------------------------------------------
def print_options(options, title=None, default=None):
  if title:
    out(layout(title))
  maxwid = len(str(len(options)))
  for idx, opt in enumerate(options):
    if morph.isstr(opt):
      lbl = opt
      opt = idx
    else:
      opt, lbl = opt
    if default is not None and default == opt:
      out(_(' *{index: >{width}}. {label}', index=idx + 1, width=maxwid, label=lbl))
    else:
      out(_('  {index: >{width}}. {label}', index=idx + 1, width=maxwid, label=lbl))
  out()

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
    help=_('switch the default processing of any EXPR and GLOB parameter to'
           ' use regular expressions (the default is to respectively use'
           ' natural language and cocoon-style glob matching)'))

  common.add_argument(_('--warranty'), action=WarrantyAction, warranty=WARRANTY)

  return common

#------------------------------------------------------------------------------
def run(cli, args, features=None):

  from .config import cmd_config

  options = cli.parse_args(args=args)

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
    return run_check(options.call, options, options)
  if options.call is cmd_config:
    return run_check(options.call, options, options)

  try:
    options.engine = engine.Engine(options.config)
  except engine.ConfigError as e:
    cli.error(e)

  try:
    options.profile = options.engine.getProfile(options.profile)
  except KeyError:
    cli.error(_('profile "{}" not found', options.profile))

  if options.profile.driver.features.sync:
    options.profile.sync()

  if features:
    driver = options.profile.driver
    for feature, version in features.items():
      # todo: perhaps use setuptools' version comparison
      #       and requirements facility
      if driver.features.get(feature) != version:
        cli.error(_('profile driver "{}" does not support feature "{}"',
                    driver.name, feature))

  # TODO: ==> in multi-query/glob mode, allow per-query/glob regex control...
  if getattr(options, 'query', False):
    options.query = ( 'regex:' if options.regex else 'query:') \
      + options.query
  # todo: if secnote, check that secure notes are supported by the active vault...
  if getattr(options, 'glob', False):
    options.glob = ( 'regex:' if options.regex else 'glob:') \
      + options.glob

  return run_check(options.call, options, options, options.profile)

#------------------------------------------------------------------------------
def run_check(cmd, options, *args, **kw):
  try:
    return cmd(*args, **kw)
  except ProgramExit as err:
    return err.message
  except api.Error as err:
    log.debug(
      'failed during execution of %s:', cmd.__name__, exc_info=True)
    out('[**] ERROR: {}: {}'.format(err.__class__.__name__, err.message),
        file=sys.stderr)
    return 100

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
