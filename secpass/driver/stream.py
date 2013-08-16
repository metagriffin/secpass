# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/22
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

# TODO: add ability to only store N latest records for any given ID
#       (to limit file size blow-up)

import time, uuid, csv, re, copy
from secpass import api
from secpass.driver import base
from secpass.util import glob2re

#------------------------------------------------------------------------------
class StreamEntry(api.Entry):
  def __init__(self,
               created=None, updated=None, lastused=None, deleted=None,
               **kw):
    super(StreamEntry, self).__init__(**kw)
    self.created  = None if created == '' or created is None else float(created)
    self.updated  = None if updated == '' or updated is None else float(updated)
    self.lastused = None if lastused == '' or lastused is None else float(lastused)
    self.deleted  = None if deleted == '' or deleted is None else float(deleted)
  def clearPassword(self):
    self.password = None
    return self

#------------------------------------------------------------------------------
class AbstractStreamDriver(base.Driver):

  PARAMS = ()

  FIELDS = ('id', 'seq', 'created', 'updated', 'lastused', 'deleted') \
    + api.Entry.PROFILE_ITEMS

  #----------------------------------------------------------------------------
  def __init__(self, *args, **kw):
    pass

  #----------------------------------------------------------------------------
  def create(self, entry):
    new = StreamEntry(id=str(uuid.uuid4()), seq=0)
    for fld in api.Entry.PROFILE_ITEMS:
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
    new.seq += 1
    new.updated = new.lastused = time.time()
    for fld in api.Entry.PROFILE_ITEMS:
      setattr(new, fld, getattr(entry, fld))
    self.saveEntries(entries + [new])
    return new

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
    if not expr:
      expr = None
    elif expr.startswith('regex:'):
      expr = re.compile(expr[6:], flags=re.IGNORECASE)
    else:
      expr = re.compile(glob2re(expr), flags=re.IGNORECASE)
    ret = []
    for entry in self.getEntries():
      if not expr or self._matches(entry, expr):
        ret.append(entry)
        # if len(ret) > api.DEFAULT_LIST_MAX:
        #   raise api.LimitExceeded('too many matches')
    # todo: order the results by best match
    return [r.clearPassword() for r in ret]

  #----------------------------------------------------------------------------
  def _matches(self, entry, expr):
    # todo: compare notes too?
    return expr.search(entry.service or '') or expr.search(entry.role or '')

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
# end of $Id$
#------------------------------------------------------------------------------
