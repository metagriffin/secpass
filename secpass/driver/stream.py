# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/07/22
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

# TODO: add ability to only store N latest records for any given ID
#       (to limit file size blow-up)

import time, uuid, csv, re, copy
import globre

from secpass import api

#------------------------------------------------------------------------------
def parseFloat(value):
  if value in (None, ''):
    return None
  return float(value)

#------------------------------------------------------------------------------
class StreamEntry(api.Entry):
  def __init__(self,
               created=None, updated=None, lastused=None, deleted=None,
               **kw):
    super(StreamEntry, self).__init__(**kw)
    self.created  = parseFloat(created)
    self.updated  = parseFloat(updated)
    self.lastused = parseFloat(lastused)
    self.deleted  = parseFloat(deleted)
  def clearPassword(self):
    self.password = None
    return self

#------------------------------------------------------------------------------
class AbstractStreamStore(api.Store):

  FIELDS = ('id', 'seq', 'created', 'updated', 'lastused', 'deleted') \
    + api.Entry.ATTRIBUTES

  #----------------------------------------------------------------------------
  def create(self, entry):
    new = StreamEntry(id=str(uuid.uuid4()), seq=0)
    for fld in api.Entry.ATTRIBUTES:
      setattr(new, fld, getattr(entry, fld))
    new.deleted = None
    new.created = new.updated = new.lastused = time.time()
    self.saveEntries(list(self.loadEntries()) + [new])
    return new

  #----------------------------------------------------------------------------
  def read(self, entry_id):
    cur = None
    entries = list(self.loadEntries())
    for test in entries:
      if entry_id == test.id and ( cur is None or cur.seq < test.seq ):
        cur = test
    if cur is None or cur.deleted is not None:
      raise api.EntryNotFound(entry_id)
    new = copy.deepcopy(cur)
    new.seq += 1
    new.lastused = time.time()
    self.saveEntries(entries + [new])
    return new

  #----------------------------------------------------------------------------
  def update(self, entry):
    if not entry.id:
      raise api.EntryNotFound(entry_id)
    cur = None
    entries = list(self.loadEntries())
    for test in entries:
      if entry.id == test.id and ( cur is None or cur.seq < test.seq ):
        cur = test
    if cur is None:
      raise api.EntryNotFound(entry_id)
    new = copy.deepcopy(cur)
    for fld in api.Entry.ATTRIBUTES:
      setattr(new, fld, getattr(entry, fld))
    new.seq += 1
    new.updated = new.lastused = time.time()
    self.saveEntries(entries + [new])
    return new

  #----------------------------------------------------------------------------
  def modify(self, entry_id, **kw):
    cur = None
    entries = list(self.loadEntries())
    for test in entries:
      if entry_id == test.id and ( cur is None or cur.seq < test.seq ):
        cur = test
    if cur is None or cur.deleted is not None:
      raise api.EntryNotFound(entry_id)
    new = copy.deepcopy(cur)
    new.update(kw)
    new.seq += 1
    new.updated = new.lastused = time.time()
    self.saveEntries(entries + [new])
    return True

  #----------------------------------------------------------------------------
  def delete(self, entry_id):
    cur = None
    entries = list(self.loadEntries())
    for test in entries:
      if entry_id == test.id and ( cur is None or cur.seq < test.seq ):
        cur = test
    if cur is None:
      raise api.EntryNotFound(entry_id)
    new = copy.deepcopy(cur)
    new.seq += 1
    new.deleted = time.time()
    self.saveEntries(entries + [new])

  #----------------------------------------------------------------------------
  def find(self, expr=None):
    # todo: use pylucene?...
    if not expr:
      expr = None
    elif expr.startswith('regex:'):
      expr = re.compile(expr[6:], flags=re.IGNORECASE)
    else:
      if expr.startswith('query:'):
        expr = expr[6:]
      # todo: is this really the best natural language evaluation?...
      expr = globre.compile(expr, flags=re.IGNORECASE)
    ret = self.getEntries()
    if expr:
      # todo: order the results by best match
      ret = [entry for entry in ret if self._matches(entry, expr)]
    return [r.clearPassword() for r in ret]

  #----------------------------------------------------------------------------
  def _matches(self, entry, expr):
    return (
      expr.search(entry.service or '')
      or expr.search(entry.role or '')
      or expr.search(entry.notes or ''))

  #----------------------------------------------------------------------------
  def getEntries(self):
    ret = dict()
    for entry in self.loadEntries():
      if entry.id not in ret \
          or entry.seq > ret[entry.id].seq:
        ret[entry.id] = entry
    for entry in ret.values():
      if entry.deleted is not None:
        continue
      yield entry

  #----------------------------------------------------------------------------
  def loadEntries(self):
    with self.openReadStream() as fp:
      csvr = csv.reader(fp, quoting=csv.QUOTE_NONNUMERIC)
      hdrs = csvr.next()
      cnt  = 0
      for row in csvr:
        cnt += 1
        if len(hdrs) != len(row):
          raise api.IntegrityError(
            'stream entry {} column count mismatch (expected {}, got {})'.format(
            cnt, len(hdrs), len(row)))
        yield StreamEntry(**dict(zip(hdrs, row)))

  #----------------------------------------------------------------------------
  def saveEntries(self, entries):
    with self.openWriteStream() as fp:
      csvw = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
      csvw.writerow(self.FIELDS)
      for record in entries:
        csvw.writerow([getattr(record, fld) for fld in self.FIELDS])

  #----------------------------------------------------------------------------
  def openReadStream(self):
    raise NotImplementedError()

  #----------------------------------------------------------------------------
  def openWriteStream(self):
    raise NotImplementedError()

#------------------------------------------------------------------------------
class AbstractStreamDriver(api.Driver):

  #----------------------------------------------------------------------------
  def __init__(self, *args, **kw):
    super(AbstractStreamDriver, self).__init__(*args, **kw)
    self.features.secpass = True

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
