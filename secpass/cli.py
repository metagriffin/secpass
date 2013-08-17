# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/25
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

# TODO: i18n...

import sys, os, os.path, logging, argparse, ConfigParser, math, getpass
import pkg_resources
from . import api, engine, util
from .util import adict, zulu, localtime, resolvePath, asbool, resolve

#------------------------------------------------------------------------------
DEFAULT_SHOW_MAX    = 3
DEFAULT_CONFIG_DATA = pkg_resources.resource_string('secpass', 'res/config.ini')

#------------------------------------------------------------------------------
log = logging.getLogger(__name__)
rootlog = logging.getLogger()
rootlog.setLevel(logging.WARNING)
rootlog.addHandler(logging.StreamHandler())
# TODO: add a logging formatter...

#------------------------------------------------------------------------------
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
  lead = '{} entr{} matched:'.format(len(records), 'y' if len(records) == 1 else 'ies')
  while True:
    print lead
    printEntries(options, records)
    try:
      prompt = 'Which ones do you want {} ("all" [default], "none", or specific numbers)? '.format(
        action)
      choice = raw_input(prompt).strip().lower()
    except EOFError:
      print '^D'
      raise ProgramExit(20)
    except KeyboardInterrupt:
      print ''
      raise ProgramExit(21)
    if choice == 'none':
      return []
    if choice in ('all', ''):
      break
    try:
      # todo: allow range specs, eg '1-4' or '1 through 4', etc.
      choice = [int(c) for c in choice.replace(',', ' ').split()]
    except ValueError:
      lead = 'Hmm. I expected a number (or list thereof)... please try again:'
      continue
    if len([c for c in choice if c < 1 or c > len(records)]) > 0:
      lead = 'Hmm. I expected numbers between 1 and {}... please try again:' \
        .format(len(records))
      continue
    if len(choice) <= 0:
      lead = 'Hmm. I expected at least one entry number... please try again:'
      continue
    records = [rec for idx, rec in enumerate(records) if idx + 1 in choice]
    break
  if len(records) <= 0:
    return []
  lead = 'The following {} {} will be {}:'.format(
    len(records), 'entry' if len(records) == 1 else 'entries', action)
  while True:
    print lead
    printEntries(options, records)
    try:
      choice = raw_input('Are you sure (y/N)? ').strip().lower()
    except EOFError:
      print '^D'
      raise ProgramExit(20)
    except KeyboardInterrupt:
      print ''
      raise ProgramExit(21)
    if not asbool(choice):
      print 'Operation aborted.'
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
    print 'The following entr{} {} similar:'.format(
      'y' if len(matches) == 1 else 'ies',
      'is' if len(matches) == 1 else 'are')
    printEntries(options, matches)
    try:
      create = raw_input('Continue with entry creation (y/N)? ')
    except EOFError:
      print '^D'
      return 20
    except KeyboardInterrupt:
      print ''
      return 21
    if not asbool(create):
      print 'Operation aborted.'
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
    print 'Setting password to "{entry.password}" for {entry.role} @ {entry.service}.'\
      .format(entry=entry)
  engine.create(entry)
  return 0

#------------------------------------------------------------------------------
def cmd_get(options, engine):
  # USAGE: get [-h] [-r] EXPR
  # todo: check options.regex
  # todo: catch LimitExceeded
  records = engine.find(options.search)
  if len(records) <= 0:
    if options.search:
      print 'No entries matched "{}".'.format(options.search)
    else:
      print 'No entries found.'
    return 0
  if len(records) > DEFAULT_SHOW_MAX:
    if options.search:
      lead = 'Too many entries matched "{}":'.format(options.search)
    else:
      lead = 'Too many entries:'
    while True:
      print lead
      printEntries(options, records)
      try:
        choice = raw_input('Your choice? ').strip()
      except EOFError:
        print '^D'
        return 20
      except KeyboardInterrupt:
        print ''
        return 21
      try:
        idx = int(choice)
      except ValueError:
        lead = 'Hmm. I expected a number... please try again:'
        continue
      if idx < 1 or idx > len(records):
        lead = 'Hmm. I expected a number between 1 and {}... please try again:' \
          .format(len(records))
        continue
      records = [records[idx - 1]]
      break
  records = [engine.read(record.id) for record in records]
  print 'Selected entr{}:'.format('y' if len(records) == 1 else 'ies')
  printEntries(options, records, passwords=True)
  return 0

#------------------------------------------------------------------------------
def cmd_set(options, engine):
  # USAGE: set [-h] [-r] [-f] [-o] [-n NOTES] EXPR [PASSWORD]
  # todo: check options.regex
  records = engine.find(options.search)
  if len(records) <= 0:
    if options.search:
      print 'No entries matched "{}".'.format(options.search)
    else:
      print 'No entries found.'
    return 0
  if not options.force:
    records = selectEntries(options, records, 'modified')
  if len(records) <= 0:
    return 0
  for record in records:
    try:
      display, newpass = getPassword(
        options, 'New password for {entry.role} @ {entry.service}: '.format(
          entry=record))
    except EOFError:
      print '^D'
      return 20
    except KeyboardInterrupt:
      print '^C'
      return 21
    record.password = newpass
    if display:
      print 'Setting password to "{entry.password}" for {entry.role} @ {entry.service}.'\
        .format(entry=record)
    if options.overwrite:
      notes = options.notes
    else:
      notes = '\n'.join([record.notes or '', options.notes or '']).strip()
    engine.update(record)
  print '{} {} modified.'.format(
    len(records), 'entry' if len(records) == 1 else 'entries')
  return 0

#------------------------------------------------------------------------------
def cmd_delete(options, engine):
  # USAGE: delete [-h] [-r] [-f] EXPR
  # todo: check options.regex
  records = engine.find(options.search)
  if len(records) <= 0:
    if options.search:
      print 'No entries matched "{}".'.format(options.search)
    else:
      print 'No entries found.'
    return 0
  if not options.force:
    records = selectEntries(options, records, 'deleted')
  if len(records) <= 0:
    return 0
  for record in records:
    engine.delete(record.id)
  print '{} {} deleted.'.format(
    len(records), 'entry' if len(records) == 1 else 'entries')
  return 0

#------------------------------------------------------------------------------
def cmd_list(options, engine):
  # USAGE: list [-h] [-r] [EXPR]
  # todo: check options.regex
  records = engine.find(options.search)
  if len(records) <= 0:
    if options.search:
      print 'No entries matched "{}".'.format(options.search)
    else:
      print 'No entries found.'
    return 0
  if options.search:
    print 'Entries matching "{}":'.format(options.search or 'all')
  else:
    print 'All entries:'
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
      print >>sys.stderr, 'file "%s" exists -- use "--force" to overwrite' \
        % (options.config,)
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

  cli = argparse.ArgumentParser(
    #usage      = '%(prog)s [-h|--help] [OPTIONS] COMMAND [CMD-OPTIONS] ...',
    description = 'Secure Passwords',
    epilog      = '''
      Whenever a PASSWORD option is accepted, you can specify either
      the literal password, "-", or nothing at all. The literal "-"
      will cause secpass to prompt for the password, which is much
      more secure than providing the password on the command line (and
      is therefore the recommended approach). If not specified or
      empty, it will be auto-generated (and displayed).
      '''
    )

  cli.register('action', 'parsers', AliasedSubParsersAction)

  cli.add_argument(
    '-v', '--verbose',
    action='count', default=0,
    help='increase verbosity (can be specified multiple times)')

  cli.add_argument(
    '-c', '--config', metavar='FILENAME',
    default=defconf,
    help='configuration filename (default: "%(default)s")')

  cli.add_argument(
    '-p', '--profile', metavar='PROFILE',
    help='configuration profile id or name')

  subcmds = cli.add_subparsers(
    dest='command',
    title='Commands',
    help='command (use "%(prog)s [COMMAND] --help" for details)')

  # TODO: re-enable the aliases... but first figure out how to
  #       eliminate the aliases from the list of available commands
  #       in the help text.

  # INIT command
  subcli = subcmds.add_parser(
    'init', #aliases=('i', 'ini',),
    help='create initial secpass configuration file')
  subcli.add_argument(
    '-f', '--force',
    action='store_true',
    help='force overwrite of existing configuration file')
  subcli.set_defaults(call=cmd_init)

  # ADD command
  subcli = subcmds.add_parser(
    'add', #aliases=('a',),
    help='add a new entry')
  subcli.add_argument(
    '-n', '--notes',
    help='set the notes for the entry')
  subcli.add_argument(
    'service', metavar='SERVICE',
    help='service, domain, URL, or other identifier')
  subcli.add_argument(
    'role', metavar='ROLE',
    help='role or username for the service')
  subcli.add_argument(
    'password', metavar='PASSWORD',
    nargs='?',
    help='new password (if "-" it will be prompted for, if empty or' \
         ' unspecified it will be auto-generated)')
  subcli.set_defaults(call=cmd_add)

  # SET command
  subcli = subcmds.add_parser(
    'set', #aliases=('s', 'update', 'u', 'rotate', 'rot', 'rt'),
    help='update/rotate an existing entry')
  subcli.add_argument(
    '-r', '--regex',
    action='store_true',
    help='specifies that EXPR is a regular expression')
  subcli.add_argument(
    '-f', '--force',
    action='store_true',
    help='update all matches without prompting for confirmation')
  subcli.add_argument(
    '-o', '--overwrite',
    action='store_true',
    help='replace the current notes instead of appending')
  subcli.add_argument(
    '-n', '--notes',
    help='append to the current notes for the entry')
  subcli.add_argument(
    'search', metavar='EXPR',
    help='expression (list of keywords) to search for in the database')
  subcli.add_argument(
    'password', metavar='PASSWORD',
    nargs='?',
    help='new password (if "-" it will be prompted for, if empty or' \
         ' unspecified it will be auto-generated)')
  subcli.set_defaults(call=cmd_set)

  # GET command
  subcli = subcmds.add_parser(
    'get', #aliases=('g', ),
    help='retrieve a secure password')
  subcli.add_argument(
    '-r', '--regex',
    action='store_true',
    help='specifies that EXPR is a regular expression')
  subcli.add_argument(
    'search', metavar='EXPR',
    help='expression (list of keywords) to search for in the database')
  subcli.set_defaults(call=cmd_get)

  # DELETE command
  subcli = subcmds.add_parser(
    'delete', #aliases=('del', 'd', 'remove', 'rem', 'rm'),
    help='remove an entry')
  subcli.add_argument(
    '-r', '--regex',
    action='store_true',
    help='specifies that EXPR is a regular expression')
  subcli.add_argument(
    '-f', '--force',
    action='store_true',
    help='delete all matches without prompting for confirmation')
  subcli.add_argument(
    'search', metavar='EXPR',
    help='expression (list of keywords) to search for in the database')
  subcli.set_defaults(call=cmd_delete)

  # LIST command
  subcli = subcmds.add_parser(
    'list', #aliases=('ls', 'l', 'find', 'f', 'grep', 'search'),
    help='search for an entry')
  subcli.add_argument(
    '-r', '--regex',
    action='store_true',
    help='specifies that EXPR is a regular expression')
  subcli.add_argument(
    'search', metavar='EXPR',
    nargs='?',
    help='expression (list of keywords) to search for in the database')
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
        'configuration "%s" does not exist -- use "%s init" to create it'
        % (options.config, cli.prog))
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
    cli.error('profile "%s" not found' % (options.profile,))

  try:
    return options.call(options, options.profile)
  except ProgramExit as e:
    return e.message

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
