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

import sys, os, os.path, logging, argparse, ConfigParser, math, getpass
import pkg_resources
import morph

from .. import api, engine, util
from ..util import zulu, localtime, resolvePath, _

#------------------------------------------------------------------------------
DEFAULT_SHOW_MAX    = 3
DEFAULT_CONFIG_DATA = pkg_resources.resource_string('secpass', 'res/config.ini')

#------------------------------------------------------------------------------
log = logging.getLogger(__name__)
rootlog = logging.getLogger()
rootlog.setLevel(logging.WARNING)
rootlog.addHandler(logging.StreamHandler())
# TODO: add a logging formatter...
# TODO: configure logging from config.ini?...

#------------------------------------------------------------------------------
# todo: i18n...
basefmt  = '  {idx: >{wid}}. {record.role: <{rwid}} @ {record.service: <{swid}}'
pwfmt    = basefmt + ' : {record.password}'
creatfmt = basefmt + ' (created {created}, last used {lastused})'
modiffmt = basefmt + ' (created {created}, updated {updated}, last used {lastused})'
def printEntries(options, records, passwords=False):
  wid  = 1 + int(math.floor(math.log10(len(records))))
  rwid = max([len(record.role or '') for record in records])
  swid = max([len(record.service or '') for record in records])
  for idx, record in enumerate(records):
    fmt = basefmt
    if options.verbose:
      fmt = creatfmt if record.created == record.updated else modiffmt
    if passwords:
      fmt = pwfmt
    print fmt.format(idx=idx + 1, wid=wid, rwid=rwid, swid=swid, record=record,
                     created=localtime(record.created, ms=False),
                     updated=localtime(record.updated, ms=False),
                     lastused=localtime(record.lastused, ms=False),
                     )

#------------------------------------------------------------------------------
class ProgramExit(Exception): pass

#------------------------------------------------------------------------------
def selectEntries(options, records, action):
  if len(records) <= 0:
    return []
  if len(records) == 1:
    lead = _('1 entry matched:')
  else:
    lead = _('{} entries matched:', len(records))
  while True:
    print lead
    printEntries(options, records)
    try:
      prompt = _('Which ones do you want {action} ("all" [default], "none", or specific numbers)? ',
                 action=action)
      choice = raw_input(prompt).strip().lower()
    except EOFError:
      print '^D'
      raise ProgramExit(20)
    except KeyboardInterrupt:
      print ''
      raise ProgramExit(21)
    if choice == _('none'):
      return []
    if choice in (_('all'), ''):
      break
    try:
      # todo: allow range specs, eg '1-4' or '1 through 4', etc.
      choice = [int(c) for c in choice.replace(',', ' ').split()]
    except ValueError:
      lead = _('Hmm. I expected a number (or list thereof)... please try again:')
      continue
    if len([c for c in choice if c < 1 or c > len(records)]) > 0:
      lead = _('Hmm. I expected numbers between 1 and {}... please try again:',
               len(records))
      continue
    if len(choice) <= 0:
      lead = _('Hmm. I expected at least one entry number... please try again:')
      continue
    records = [rec for idx, rec in enumerate(records) if idx + 1 in choice]
    break
  if len(records) <= 0:
    return []
  lead = _('The following {count} {entry} will be {action}:',
           count  = len(records),
           entry  = _('entry') if len(records) == 1 else _('entries'),
           action = action)
  while True:
    print lead
    printEntries(options, records)
    try:
      choice = raw_input(_('Are you sure (y/N)? ')).strip().lower()
    except EOFError:
      print '^D'
      raise ProgramExit(20)
    except KeyboardInterrupt:
      print ''
      raise ProgramExit(21)
    if not morph.tobool(choice):
      print _('Operation aborted.')
      raise ProgramExit(22)
    break
  return records

#------------------------------------------------------------------------------
def getPassword(options, prompt=None):
  if options.password == '-':
    if prompt:
      return False, getpass.getpass(prompt=prompt)
    else:
      return False, getpass.getpass()
  if options.password is not None:
    return False, options.password
  return (True, util.generatePassword(options.profile.settings))

#------------------------------------------------------------------------------
def cmd_add(options, engine):
  # USAGE: add [-h] [-n NOTES] SERVICE ROLE [PASSWORD]
  notes = options.notes
  # todo: improve this similarity check...
  matches = [e for e in engine.find()
             if e.service == options.service]# and e.role == options.role]
  if len(matches) > 0:
    if len(matches) == 1:
      print _('The following entry is similar:')
    else:
      print _('The following entries are similar:')
    printEntries(options, matches)
    try:
      create = raw_input(_('Continue with entry creation (y/N)? '))
    except EOFError:
      print '^D'
      return 20
    except KeyboardInterrupt:
      print ''
      return 21
    if not morph.tobool(create):
      print _('Operation aborted.')
      return 22
  try:
    display, newpass = getPassword(options)
  except EOFError:
    print '^D'
    return 20
  except KeyboardInterrupt:
    print '^C'
    return 21
  entry = api.Entry(
    service=options.service, role=options.role,
    password=newpass, notes=notes)
  if display:
    print _('Setting password to "{entry.password}" for {entry.role} @ {entry.service}.',
            entry=entry)
  engine.create(entry)
  return 0

#------------------------------------------------------------------------------
def cmd_get(options, engine):
  # USAGE: get [-h] [-r] EXPR
  # todo: catch LimitExceeded
  records = engine.find(options.query)
  if len(records) <= 0:
    if options.query:
      print _('No entries matched "{}".', options.query.split(':', 1)[1])
    else:
      print _('No entries found.')
    return 0
  if len(records) > DEFAULT_SHOW_MAX:
    if options.query:
      lead = _('Too many entries matched "{}":', options.query.split(':', 1)[1])
    else:
      lead = _('Too many entries:')
    while True:
      print lead
      printEntries(options, records)
      try:
        choice = raw_input(_('Your choice? ')).strip()
      except EOFError:
        print '^D'
        return 20
      except KeyboardInterrupt:
        print ''
        return 21
      try:
        idx = int(choice)
      except ValueError:
        lead = _('Hmm. I expected a number... please try again:')
        continue
      if idx < 1 or idx > len(records):
        lead = _('Hmm. I expected a number between 1 and {}... please try again:',
                 len(records))
        continue
      records = [records[idx - 1]]
      break
  records = [engine.read(record.id) for record in records]
  if len(records) == 1:
    print _('Selected entry:')
  else:
    print _('Selected entries:')
  printEntries(options, records, passwords=True)
  return 0

#------------------------------------------------------------------------------
def cmd_set(options, engine):
  # USAGE: set [-h] [-r] [-f] [-o] [-n NOTES] EXPR [PASSWORD]
  records = engine.find(options.query)
  if len(records) <= 0:
    if options.query:
      print _('No entries matched "{}".', options.query.split(':', 1)[1])
    else:
      print _('No entries found.')
    return 0
  if not options.force:
    records = selectEntries(options, records, _('modified'))
  if len(records) <= 0:
    return 0
  for record in records:
    try:
      display, newpass = getPassword(
        options, _('New password for {entry.role} @ {entry.service}: ',
                   entry=record))
    except EOFError:
      print '^D'
      return 20
    except KeyboardInterrupt:
      print '^C'
      return 21
    record.password = newpass
    if options.overwrite:
      notes = options.notes
    else:
      notes = '\n'.join([record.notes or '', options.notes or '']).strip()
    if options.service is not None:
      record.service = options.service
    if options.role is not None:
      record.role = options.role
    if display:
      print _('Setting password to "{entry.password}" for {entry.role} @ {entry.service}.',
              entry=record)
    engine.update(record)
  if len(records) == 1:
    print _('1 entry modified.')
  else:
    print _('{} entries modified.', len(records))
  return 0

#------------------------------------------------------------------------------
def cmd_delete(options, engine):
  # USAGE: delete [-h] [-r] [-f] EXPR
  records = engine.find(options.query)
  if len(records) <= 0:
    if options.query:
      print _('No entries matched "{}".', options.query.split(':', 1)[1])
    else:
      print _('No entries found.')
    return 0
  if not options.force:
    records = selectEntries(options, records, _('deleted'))
  if len(records) <= 0:
    return 0
  for record in records:
    engine.delete(record.id)
  if len(records) == 1:
    print _('1 entry deleted.')
  else:
    print _('{} entries deleted.', len(records))
  return 0

#------------------------------------------------------------------------------
def cmd_list(options, engine):
  # USAGE: list [-h] [-r] [EXPR]
  records = engine.find(options.query)
  if len(records) <= 0:
    if options.query:
      print _('No entries matched "{}".', options.query.split(':', 1)[1])
    else:
      print _('No entries found.')
    return 0
  if options.query:
    print _('Entries matching "{}":', options.query.split(':', 1)[1])
  else:
    print _('All entries:')
  printEntries(options, records)
  return 0

#------------------------------------------------------------------------------
# command aliasing, shamelessly scrubbed from:
#   https://gist.github.com/sampsyo/471779
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
def cmd_init(options):
  # USAGE: init [-h] [-f]
  if os.path.exists(options.config):
    if not options.force:
      print >>sys.stderr, _('file "{}" exists -- use "--force" to overwrite',
                            options.config)
      return 20
  cdir = os.path.dirname(options.config)
  if not os.path.isdir(cdir):
    os.makedirs(cdir)
  with open(options.config, 'wb') as fp:
    fp.write(DEFAULT_CONFIG_DATA)
  return 0

#------------------------------------------------------------------------------
def main(argv=None):

  defconf = os.environ.get('SECPASS_CONFIG', api.DEFAULT_CONFIG)

  common = argparse.ArgumentParser(add_help=False)

  common.add_argument(
    _('-v'), _('--verbose'),
    dest='verbose', action='count', default=0,
    help=_('increase verbosity (can be specified multiple times)'))

  common.add_argument(
    _('-c'), _('--config'), metavar=_('FILENAME'),
    dest='config', default=defconf,
    help=_('configuration filename (current default: "{}")', '%(default)s'))

  common.add_argument(
    _('-p'), _('--profile'), metavar=_('PROFILE'),
    dest='profile',
    help=_('configuration profile id or name'))

  common.add_argument(
    _('-r'), _('--regex'),
    dest='regex', action='store_true',
    help=_('specifies that any EXPR is a regular expression (the default'
           ' is to use natural-language evaluation)'))

  cli = argparse.ArgumentParser(
    parents     = [common],
    #usage      = '%(prog)s [-h|--help] [OPTIONS] COMMAND [CMD-OPTIONS] ...',
    description = _('Secure Passwords'),
    epilog      = _('''
      Whenever a PASSWORD option is accepted, you can specify either
      the literal password, "-", or nothing at all. The literal "-"
      will cause secpass to prompt for the password, which is much
      more secure than providing the password on the command line (and
      is therefore the recommended approach). If not specified or
      empty, it will be auto-generated (and displayed).
      ''')
    )

  cli.register('action', 'parsers', AliasedSubParsersAction)

  subcmds = cli.add_subparsers(
    dest='command',
    title=_('Commands'),
    help=_('command (use "{} [COMMAND] --help" for details)', '%(prog)s'))

  # TODO: re-enable the aliases... but first figure out how to
  #       eliminate the aliases from the list of available commands
  #       in the help text.

  # INIT command
  subcli = subcmds.add_parser(
    _('init'), #aliases=('i', 'ini',),
    parents=[common],
    help=_('create initial secpass configuration file'))
  subcli.add_argument(
    _('-f'), _('--force'),
    dest='force', action='store_true',
    help=_('force overwrite of existing configuration file'))
  subcli.set_defaults(call=cmd_init)

  # ADD command
  subcli = subcmds.add_parser(
    _('add'), #aliases=('a',),
    parents=[common],
    help=_('add a new entry'))
  subcli.add_argument(
    _('-n'), _('--notes'),
    dest='notes',
    help=_('set the notes for the entry'))
  subcli.add_argument(
    _('service'), metavar=_('SERVICE'),
    help=_('service, domain, URL, or other identifier'))
  subcli.add_argument(
    _('role'), metavar=_('ROLE'),
    help=_('role or username for the service'))
  subcli.add_argument(
    _('password'), metavar=_('PASSWORD'),
    nargs='?',
    help=_('new password (if "-" it will be prompted for, if empty or' \
             ' unspecified it will be auto-generated)'))
  subcli.set_defaults(call=cmd_add)

  # SET command
  subcli = subcmds.add_parser(
    _('set'), #aliases=('s', 'update', 'u', 'rotate', 'rot', 'rt'),
    parents=[common],
    help=_('update/rotate an existing entry'))
  subcli.add_argument(
    _('-f'), _('--force'),
    dest='force', action='store_true',
    help=_('update all matches without prompting for confirmation'))
  subcli.add_argument(
    _('-o'), _('--overwrite'),
    dest='overwrite', action='store_true',
    help=_('replace the current notes instead of appending'))
  subcli.add_argument(
    _('-n'), _('--notes'),
    dest='notes',
    help=_('append to the current notes for the entry'))
  subcli.add_argument(
    _('-s'), _('--service'),
    dest='service',
    help=_('update the entry\'s service (e.g. domain, URL, etc)'))
  subcli.add_argument(
    _('-R'), _('--role'),
    dest='role',
    help=_('update the entry\'s role (e.g. username)'))
  subcli.add_argument(
    _('query'), metavar=_('EXPR'),
    help=_('expression (list of keywords) to search for in the database'))
  subcli.add_argument(
    _('password'), metavar=_('PASSWORD'),
    nargs='?',
    help=_('new password (if "-" it will be prompted for, if empty or'
           ' unspecified it will be auto-generated)'))
  subcli.set_defaults(call=cmd_set)

  # GET command
  subcli = subcmds.add_parser(
    _('get'), #aliases=('g', ),
    parents=[common],
    help=_('retrieve a secure password'))
  subcli.add_argument(
    _('query'), metavar=_('EXPR'),
    help=_('expression (list of keywords) to search for in the database'))
  subcli.set_defaults(call=cmd_get)

  # DELETE command
  subcli = subcmds.add_parser(
    _('delete'), #aliases=('del', 'd', 'remove', 'rem', 'rm'),
    parents=[common],
    help=_('remove an entry'))
  subcli.add_argument(
    _('-f'), _('--force'),
    dest='force', action='store_true',
    help=_('delete all matches without prompting for confirmation'))
  subcli.add_argument(
    _('query'), metavar=_('EXPR'),
    help=_('expression (list of keywords) to search for in the database'))
  subcli.set_defaults(call=cmd_delete)

  # LIST command
  # todo: if `grep` is used, assume regex=true
  subcli = subcmds.add_parser(
    _('list'), #aliases=('ls', 'l', 'find', 'f', 'grep', 'search', 'query'),
    parents=[common],
    help=_('search for an entry'))
  subcli.add_argument(
    _('query'), metavar=_('EXPR'),
    nargs='?',
    help=_('expression (list of keywords) to search for (if'
           ' unspecified, lists all entries in the profile)'))
  subcli.set_defaults(call=cmd_list)

  options = cli.parse_args(args=argv)

  if options.verbose == 1:
    rootlog.setLevel(logging.INFO)
  elif options.verbose > 1:
    rootlog.setLevel(logging.DEBUG)

  options.config = resolvePath(options.config)

  if not os.path.isfile(options.config):
    if options.call is not cmd_init:
      cli.error(
        _('configuration "{}" does not exist -- use "{prog} init" to create it',
          options.config, prog=cli.prog))
    return options.call(options)
  if options.call is cmd_init:
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
    if getattr(options, 'query', False):
      options.query = ( 'regex:' if options.regex else 'query:') \
        + options.query
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
