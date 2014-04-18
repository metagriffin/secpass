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

import sys
import os
import logging
import argparse
import math
import re
import morph
import hashlib

from .. import api, engine, util
from ..util import localtime, resolvePath, _
from .base import \
  ProgramExit, AliasedSubParsersAction, FuzzyChoiceArgumentParser, \
  makeCommonOptions, ask, confirm, confirmOrExit, run
from .config import addConfigCommand

#------------------------------------------------------------------------------
log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
fmt_base   = '  {idx: >{wid}}. {note.name}'
fmt_baseid = fmt_base + ' (id: {note.id})'
def printNotes(options, notes, content=False):
  wid  = 1 + int(math.floor(math.log10(len(notes))))
  for idx, note in enumerate(notes):
    showids = options.verbose or options.showids
    fmt = fmt_base if not showids else fmt_baseid
    print fmt.format(
      idx=idx + 1, wid=wid, note=note, created=localtime(note.created, ms=False))

#------------------------------------------------------------------------------
def selectNotes(options, notes, action):
  if len(notes) <= 0:
    return []
  if len(notes) == 1:
    lead = _('1 note matched:')
  else:
    lead = _('{} notes matched:', len(notes))
  while True:
    print lead
    printNotes(options, notes)
    # todo: move to use validator...
    choice = ask(
      _('Which ones do you want {action} ("all" [default], "none", or specific numbers)',
        action=action))
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
    if len([c for c in choice if c < 1 or c > len(notes)]) > 0:
      lead = _('Hmm. I expected numbers between 1 and {}... please try again:',
               len(notes))
      continue
    if len(choice) <= 0:
      lead = _('Hmm. I expected at least one note number... please try again:')
      continue
    notes = [rec for idx, rec in enumerate(notes) if idx + 1 in choice]
    break
  if len(notes) <= 0:
    return []
  lead = _('The following {count} {note} will be {action}:',
           count  = len(notes),
           note   = _('note') if len(notes) == 1 else _('notes'),
           action = action)
  print lead
  printNotes(options, notes)
  confirmOrExit(_('Are you sure'), default=False)
  return notes

#------------------------------------------------------------------------------
def cmd_set(options, engine):
  # USAGE: set [--interactive] [NAME] FILENAME
  if options.name is None:
    options.name = os.path.basename(options.filename)
  note = engine.note_find('regex:^' + re.escape(options.name) + '$')
  if not note:
    note = api.Note(name=options.name)
  else:
    note = note[0]
    if options.interactive:
      confirmOrExit(_('Note "{}" already exists: overwrite (y/N)? ', note.name))
  if options.filename == '-':
    note.content = sys.stdin.read()
  else:
    note.content = open(options.filename, 'rb').read()
  engine.note_set(note)

#------------------------------------------------------------------------------
def cmd_list(options, engine):
  # USAGE: list [GLOB]
  notes = engine.note_find(options.glob)
  if len(notes) <= 0:
    if options.glob:
      print _('No notes matched "{}".', options.glob.split(':', 1)[1])
    else:
      print _('No notes found.')
    return 0
  if options.glob:
    print _('Notes matching "{}":', options.glob.split(':', 1)[1])
  else:
    print _('All notes:')
  printNotes(options, notes)
  return 0

#------------------------------------------------------------------------------
def cmd_get(options, engine):
  # USAGE: get NAME
  note = engine.note_get(options.name)
  if not note:
    print >>sys.stderr, _('[**] ERROR: no such note "{}"', options.name)
    raise ProgramExit(10)
  sys.stdout.write(note.content)

#------------------------------------------------------------------------------
def cmd_download(options, engine):
  # USAGE: download [-d DIRECTORY] [--tree] [--purge] GLOB
  print 'TODO:NOTE.DOWNLOAD'

#------------------------------------------------------------------------------
def cmd_upload(options, engine):
  # USAGE: upload [-d DIRECTORY] [--tree] [--purge] GLOB
  print 'TODO:NOTE.UPLOAD'

#------------------------------------------------------------------------------
def cmd_delete(options, engine):
  # USAGE: 'delete' [-f] GLOB
  notes = engine.note_find(options.glob)
  if len(notes) <= 0:
    if options.glob:
      print _('No notes matched "{}".', options.glob.split(':', 1)[1])
    else:
      print _('No notes found.')
    return 0
  if not options.force:
    notes = selectNotes(options, notes, _('deleted'))
  if len(notes) <= 0:
    return 0
  for note in notes:
    engine.note_delete(note.id)
  if len(notes) == 1:
    print _('1 note deleted.')
  else:
    print _('{} note deleted.', len(notes))
  return 0

#------------------------------------------------------------------------------
def main(args=None):

  common = makeCommonOptions()

  common.add_argument(
    _('--show-ids'), _('--ids'),
    dest='showids', default=False, action='store_true',
    help=_('when showing lists of notes, also show the note IDs'))

  cli = FuzzyChoiceArgumentParser(
    parents     = [common],
    description = _('Secure (encrypted) note storage and management'),
    epilog      = _('''
      Wherever a FILENAME option is accepted, you can specify either
      the filename or "-". The latter indicates that STDIN should be
      used for input and STDOUT should be used for output. In some
      cases, the filename can be omitted completely and it will default
      to "-" handling.
      '''))

  cli.register('action', 'parsers', AliasedSubParsersAction)

  subcmds = cli.add_subparsers(
    dest='command',
    title=_('Commands'),
    help=_('command (use "{} [COMMAND] --help" for details)', '%(prog)s'))

  # TODO: maybe extend those commands that take a GLOB or FILENAME to
  #       support multiple GLOBS/FILENAMES?...

  # CONFIG command
  addConfigCommand(subcmds, common)

  # SET command
  subcli = subcmds.add_parser(
    _('set'), aliases=('add', 'create'),
    parents=[common],
    help=_('create or update the content of a secure note'))
  subcli.add_argument(
    _('-i'), _('--interactive'),
    dest='interactive', default=False, action='store_true',
    help=_('if the note with the given name already exists,'
           ' interactively prompt for confirmation before'
           ' overwriting the content'))
  subcli.add_argument(
    'name', metavar=_('NAME'),
    nargs='?',
    help=_('specify the name of the note (defaults to the filename'
           ' without any leading directories)'))
  subcli.add_argument(
    'filename', metavar=_('FILENAME'),
    help=_('the name of the file to store in the vault (if set to "-"'
           ' STDIN will be used, in which case a NAME should also be'
           ' provided)'))
  subcli.set_defaults(call=cmd_set)

  # LIST command
  # todo: if `grep` is used, assume regex=true
  subcli = subcmds.add_parser(
    _('list'), aliases=('find', 'grep', 'search', 'query'),
    parents=[common],
    help=_('search for a secure note'))
  subcli.add_argument(
    _('-s'), _('--system'),
    dest='system', default=False, action='store_true',
    help=_('show secpass system notes, i.e. ".secpass/**"'))
  subcli.add_argument(
    'glob', metavar=_('GLOB'),
    nargs='?',
    help=_('cocoon-style glob of secure note names to list (if'
           ' unspecified, lists all notes in the profile)'))
  subcli.set_defaults(call=cmd_list)

  # GET command
  subcli = subcmds.add_parser(
    _('get'), aliases=('fetch', ),
    parents=[common],
    help=_('retrieve a secure note'))
  subcli.add_argument(
    'name', metavar=_('NAME'),
    help=_('specify the name of the note to fetch'))
  subcli.set_defaults(call=cmd_get)

  # DOWNLOAD command
  subcli = subcmds.add_parser(
    _('download'),
    parents=[common],
    help=_('download multiple secure notes'))
  subcli.add_argument(
    _('-d'), _('--directory'), metavar=_('DIRECTORY'),
    dest='directory', default='.',
    help=_('specify the directory to download the notes to (defaults'
           ' to the current directory)'))
  subcli.add_argument(
    _('-t'), _('--tree'),
    dest='tree', default=False, action='store_true',
    help=_('if note names contain forward slashes ("/"), these will'
           ' be used to create a directory tree, otherwise slashes'
           ' will be URL-escaped'))
  subcli.add_argument(
    _('--purge'),
    dest='purge', default=False, action='store_true',
    help=_('delete local files that do not exist in the profile'))
  subcli.add_argument(
    _('-i'), _('--interactive'),
    dest='interactive', default=False, action='store_true',
    help=_(' interactively prompt for confirmation before'
           ' overwriting or deleting local content'))
  subcli.add_argument(
    'glob', metavar=_('GLOB'),
    nargs='?',
    help=_('cocoon-style glob of secure note names to download (if'
           ' unspecified, downloads all notes in the profile)'))
  subcli.set_defaults(call=cmd_download)

  # UPLOAD command
  subcli = subcmds.add_parser(
    _('upload'),
    parents=[common],
    help=_('upload multiple secure notes'))
  subcli.add_argument(
    _('-d'), _('--directory'), metavar=_('DIRECTORY'),
    dest='directory', default='.',
    help=_('specify the directory to upload the notes from (defaults'
           ' to the current directory)'))
  subcli.add_argument(
    _('-t'), _('--tree'),
    dest='tree', default=False, action='store_true',
    help=_('if note names contain forward slashes ("/"), these will'
           ' be used to create a directory tree, otherwise slashes'
           ' will be URL-escaped'))
  subcli.add_argument(
    _('--purge'),
    dest='purge', default=False, action='store_true',
    help=_('delete profile notes that do not exist locally'))
  subcli.add_argument(
    _('-i'), _('--interactive'),
    dest='interactive', default=False, action='store_true',
    help=_(' interactively prompt for confirmation before'
           ' overwriting or deleting remote content'))
  subcli.add_argument(
    'glob', metavar=_('GLOB'),
    nargs='?',
    help=_('cocoon-style glob of secure note names to upload (if'
           ' unspecified, uploads all notes in the directory)'))
  subcli.set_defaults(call=cmd_upload)

  # DELETE command
  subcli = subcmds.add_parser(
    _('delete'), aliases=('remove'),
    parents=[common],
    help=_('remove a secure note'))
  subcli.add_argument(
    _('-f'), _('--force'),
    dest='force', default=False, action='store_true',
    help=_('delete all matches without prompting for confirmation'))
  subcli.add_argument(
    'glob', metavar=_('GLOB'),
    help=_('cocoon-style glob of secure note names to delete'))
  subcli.set_defaults(call=cmd_delete)

  return run(cli, args, features={'secnote': 1})

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
