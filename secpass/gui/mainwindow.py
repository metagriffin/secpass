# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/08/17
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

import sys, os.path, logging, pkg_resources
from contextlib import contextmanager
import wx
from wx import xrc
import ObjectListView as OLV

from secpass import model, api, util
from secpass.util import adict, asbool, _

# todo: make the status line display the number of selected and/or
#       unselected entries

# todo: remember column sorting preference...

# todo: add control sequences to the tools, eg:
#         Ctrl-S => show passwords
#         Ctrl-H => hide passwords

#------------------------------------------------------------------------------
class NotesEditor():
  # TODO: implement...
  def __init__(self, olv, rowIndex, subItemIndex):
    pass

# <!--
#           <object class="wxTextCtrl">
#             <size>200,300</size>
#             <value>aoeu bnth cntoeh dntmoue esnth fcrho gsnhtoe hnm isnmt jsnmto.</value>
#             <style>wxSUNKEN_BORDER|wxTE_MULTILINE|wxTE_LINEWRAP</style>
#           </object>
# -->

#------------------------------------------------------------------------------
class MainWindow(object):

  #----------------------------------------------------------------------------
  def __init__(self, app):
    self.app      = app
    self.pidwid   = dict()
    self.widpid   = dict()
    self.filter   = None

  #----------------------------------------------------------------------------
  def init(self):
    self.createFrame()
    self.update()
    return True

  #----------------------------------------------------------------------------
  def close(self):
    # TODO: save settings... eg [gui] main.*, etc.
    # wx.MessageBox('Your name is %s %s!' %
    #               (self.text1.GetValue(), self.text2.GetValue()), 'Feedback')
    return self.frame.Close()

  #----------------------------------------------------------------------------
  def createFrame(self):
    self.frame     = self.app.wxres.LoadFrame(None, 'window.main')
    self.toolbar   = xrc.XRCCTRL(self.frame, 'toolbar')
    self.statusbar = xrc.XRCCTRL(self.frame, 'statusbar')
    self.menubar   = self.frame.GetMenuBar()
    self.profmenu  = None
    self.tools     = adict(
      create = self.toolbar.FindById(xrc.XRCID('tool.create')),
      edit   = self.toolbar.FindById(xrc.XRCID('tool.update')),
      rotate = self.toolbar.FindById(xrc.XRCID('tool.rotate')),
      pwcopy = self.toolbar.FindById(xrc.XRCID('tool.copy')),
      show   = self.toolbar.FindById(xrc.XRCID('tool.show')),
      hide   = self.toolbar.FindById(xrc.XRCID('tool.hide')),
      delete = self.toolbar.FindById(xrc.XRCID('tool.delete')),
      )
    self.frame.Bind(wx.EVT_MENU, self.app.OnQuit, id=wx.ID_EXIT)
    self.frame.Bind(wx.EVT_MENU, self.app.OnHelp, id=wx.ID_HELP)
    self.frame.Bind(wx.EVT_MENU, self.app.OnAbout, id=wx.ID_ABOUT)
    self.frame.Bind(wx.EVT_MENU, self.app.OnPreferences, id=wx.ID_PREFERENCES)
    self.frame.Bind(wx.EVT_MENU, self.app.OnCheckUpdate, id=xrc.XRCID('menuitem.updatecheck'))
    self.frame.Bind(wx.EVT_TEXT, self.OnFilterChange, id=xrc.XRCID('input.filter'))
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntryCreate, id=self.tools.create.Id)
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntriesUpdate, id=self.tools.edit.Id)
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntriesRotate, id=self.tools.rotate.Id)
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntryCopy, id=self.tools.pwcopy.Id)
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntriesShow, id=self.tools.show.Id)
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntriesHide, id=self.tools.hide.Id)
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntriesDelete, id=self.tools.delete.Id)
    # todo: find out why the 'about' menuitem doesn't use the standard icon...
    # todo: load window size from preferences...
    # ensure that the window is at least 600x400
    cur = self.frame.GetSize()
    cur.width  = int(self.app.getConfig('gui', 'main.width', 600))
    cur.height = int(self.app.getConfig('gui', 'main.height', 400))
    self.frame.SetSize(cur)
    self.app.SetTopWindow(self.frame)
    # setup the ObjectListView to actually show the entries
    # todo: much of this should be moved into the XRC...
    self.elbox = xrc.XRCCTRL(self.frame, 'box.entries')
    self.elview = OLV.ObjectListView(
      self.elbox, wx.ID_ANY, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
    self.elview.oddRowsBackColor  = self.app.getConfig('gui', 'main.rowcolor.odd', '#fcfcfc')
    self.elview.evenRowsBackColor = self.app.getConfig('gui', 'main.rowcolor.even', '#dedede')
    self.elview.cellEditMode      = OLV.ObjectListView.CELLEDIT_DOUBLECLICK
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.elview, 1, wx.ALL|wx.EXPAND, 0)
    self.elbox.SetSizer(sizer)
    self.elpcol = OLV.ColumnDefn(_('Profile'),
                                 valueGetter=self.getEntryProfileName,
                                 minimumWidth=10,
                                 isSpaceFilling=True,
                                 isEditable=False,
                                 )
    self.elocols = [
      OLV.ColumnDefn(_('Service'), minimumWidth=10, isSpaceFilling=True,
                     valueGetter=lambda e: e.service or _('-'), valueSetter='service',
                     ),
      OLV.ColumnDefn(_('Role'), minimumWidth=10, isSpaceFilling=True,
                     valueGetter=lambda e: e.role or _('-'), valueSetter='role',
                     ),
      OLV.ColumnDefn(_('Password'), minimumWidth=10, isSpaceFilling=True,
                     valueGetter=lambda e: e.password or _('-'), valueSetter='password',
                     ),
      OLV.ColumnDefn(_('Notes'), minimumWidth=10, isSpaceFilling=True,
                     valueGetter=lambda e: e.notes or _('-'), valueSetter='notes',
                     #cellEditorCreator=self.notesEditor
                     ),
      ]
    self.elcols = [self.elpcol] + self.elocols
    self.elview.SetColumns(self.elcols)
    self.elview.SetEmptyListMsg(_('No entries to display.'))
    self.elview.SetObjects([])
    self.elview.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnCheckSelection)
    self.elview.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnCheckSelection)
    self.frame.Show()

  #----------------------------------------------------------------------------
  def getEntryProfileName(self, entry):
    return self.app.engine.getProfile(entry.pid).name

  # #----------------------------------------------------------------------------
  # def notesEditor(self, olv, rowIndex, subItemIndex):
  #   return NotesEditor(olv, rowIndex, subItemIndex)

  #----------------------------------------------------------------------------
  def update(self):
    self.updateProfileMenu()
    self.updateToolbarTools()
    self.renderEntries()

  #----------------------------------------------------------------------------
  def updateProfileMenu(self):
    # todo: supply a patch to wx to add a getMenuById instead of this
    #       ridiculosity...
    self.pidwid = dict(((None, xrc.XRCID('menuitem.profile')),))
    if self.profmenu is None:
      self.profmenu = self.menubar.FindItemById(self.pidwid[None]).GetMenu()
    pmenu = self.profmenu
    for item in pmenu.GetMenuItems():
      pmenu.DeleteItem(item)
    pmenu.AppendCheckItem(self.pidwid[None], _('All profiles combined'),
                          _('Manage entries in all profiles'))
    pmenu.Bind(wx.EVT_MENU, self.OnProfileSwitch, id=self.pidwid[None])
    pmenu.AppendSeparator()
    def cmpprof(a, b):
      return cmp(a.name.lower(), b.name.lower())
    for profile in sorted(self.app.engine.profiles.values(), cmp=cmpprof):
      self.pidwid[profile.id] = wx.NewId()
      pmenu.AppendCheckItem(
        self.pidwid[profile.id], profile.name,
        _('Manage entries in the "{}" profile', profile.name))
      pmenu.Bind(wx.EVT_MENU, self.OnProfileSwitch, id=self.pidwid[profile.id])
    pmenu.Check(self.pidwid[self.app.pid], True)
    self.widpid = dict([[w, p] for p, w in self.pidwid.items()])

  #----------------------------------------------------------------------------
  def OnFilterChange(self, e):
    expr = e.GetEventObject().Value.strip()
    if not expr:
      expr = None
    if self.filter == expr:
      return self
    self.filter = expr
    if expr is None:
      self.elview.SetFilter(None)
    else:
      self.elview.SetFilter(OLV.Filter.TextSearch(self.elview, text=expr))
    self.elview.RepopulateList()
    # todo: figure out how to fix column widths here... (AutoSizeColumns
    # does not seem to be doing the trick...)
    self.elview.AutoSizeColumns()
    # todo: wx.EVT_LIST_ITEM_DESELECTED should really make this redundant...
    self.updateToolbarTools()
    return self

  #----------------------------------------------------------------------------
  def OnEntryCreate(self, e):
    with self.status(_('Creating new entry...')):
      if self.app.pid is None:
        # TODO: implement
        raise TypeError('CURPID IS NONE!')
      self.entryCreate(self.app.pid)

  #----------------------------------------------------------------------------
  def entryCreate(self, pid):
    profile = self.app.engine.getProfile(pid)
    entry = model.Entry(pid=pid, **profile.create(api.Entry(
      service  = _('New service'),
      role     = _('New role'),
      password = util.generatePassword(profile.settings))).asdict())
    self.addEntry(entry)
    self.elview.SelectObject(entry, deselectOthers=True, ensureVisible=True)
    self.elview.StartCellEdit(self.elview.GetIndexOf(entry),
                              1 if self.elcols[0] is self.elpcol else 0)

  #----------------------------------------------------------------------------
  def OnEntriesUpdate(self, e):
    # TODO: implement
    return self.app.NIY('Edit-via-dialog')

  #----------------------------------------------------------------------------
  def OnEntriesRotate(self, e):
    # TODO: open a 'confirm' message box...
    with self.status(_('Rotating passwords...')):
      entries = self.elview.GetSelectedObjects()
      for entry in entries:
        entry.password = util.generatePassword(
          self.app.engine.getProfile(entry.pid).settings)
        self.elview.RefreshObject(entry)
    self.updateToolbarTools()

  #----------------------------------------------------------------------------
  def OnEntryCopy(self, e):
    with self.status(_('Fetching passwords and copying to clipboard...')):
      entry = self.elview.GetSelectedObjects()[0]
      data  = entry.password
      if data is None:
        data = self.app.engine.getProfile(entry.pid).read(entry.id).password
      clip = wx.TextDataObject()
      clip.SetText(data)
      if wx.TheClipboard.IsOpened():
        return wx.MessageBox(_(
          'The clipboard is currently locked by another application'
          ' -- try again later or shut down the other application.'))
      wx.TheClipboard.Open()
      if asbool(self.app.getConfig('gui', 'clipboard.normal', 'true')):
        wx.TheClipboard.UsePrimarySelection(False)
        wx.TheClipboard.SetData(clip)
      if asbool(self.app.getConfig('gui', 'clipboard.primary', 'true')):
        wx.TheClipboard.UsePrimarySelection(True)
        wx.TheClipboard.SetData(clip)
      wx.TheClipboard.Close()

  #----------------------------------------------------------------------------
  def OnEntriesShow(self, e):
    with self.status(_('Fetching passwords...')):
      entries = self.elview.GetSelectedObjects()
      for entry in entries:
        if entry.password is not None:
          continue
        # TODO: ASYNC...
        entry.__setattr__(
          'password',
          self.app.engine.getProfile(entry.pid).read(entry.id).password,
          trigger=False)
        self.elview.RefreshObject(entry)
    self.updateToolbarTools()

  #----------------------------------------------------------------------------
  def OnEntriesHide(self, e):
    with self.status(_('Hiding passwords...')):
      entries = self.elview.GetSelectedObjects()
      for entry in entries:
        entry.__delattr__('password', trigger=False)
        self.elview.RefreshObject(entry)
    self.updateToolbarTools()

  #----------------------------------------------------------------------------
  def OnEntriesDelete(self, e):
    # TODO: open a 'confirm' message box...
    with self.status(_('Deleting entries...')):
      entries = self.elview.GetSelectedObjects()
      for entry in entries:
        self.app.engine.getProfile(entry.pid).delete(entry.id)
        self.elview.RemoveObject(entry)
    # todo: wx.EVT_LIST_ITEM_DESELECTED should really make this redundant...
    self.updateToolbarTools()

  #----------------------------------------------------------------------------
  def OnCheckSelection(self, e=None):
    self.updateToolbarTools()

  #----------------------------------------------------------------------------
  def updateToolbarTools(self):
    sel = self.elview.GetSelectedObjects()
    sellen = len(sel)
    self.toolbar.EnableTool(self.tools.create.Id, len(self.app.engine.profiles) > 0)
    self.toolbar.EnableTool(self.tools.delete.Id, sellen > 0)
    self.toolbar.EnableTool(self.tools.rotate.Id, sellen > 0)
    self.toolbar.EnableTool(self.tools.edit.Id, sellen == 1)
    self.toolbar.EnableTool(self.tools.pwcopy.Id, sellen == 1)
    vis = [e for e in sel if e.password is not None]
    self.toolbar.EnableTool(self.tools.show.Id, sellen - len(vis) > 0)
    self.toolbar.EnableTool(self.tools.hide.Id, len(vis) > 0)

  #----------------------------------------------------------------------------
  def OnProfileSwitch(self, e):
    if e.GetEventType() != wx.wxEVT_COMMAND_MENU_SELECTED:
      return
    if e.Id not in self.widpid:
      # todo: more detail / log error ...
      return wx.MessageBox(_('Internal error: unexpected WID {!r}', e.Id))
    self.app.pid = self.widpid[e.GetId()]
    if self.app.pid is not None:
      profname = self.app.engine.profiles[self.app.pid].name
      status = _('Switching to "{}" profile...', profname)
    else:
      status = _('Switching to all profiles combined...')
    with self.status(status):
      for wid in self.pidwid.values():
        self.profmenu.Check(wid, wid == e.Id)
      self.renderEntries()

  #----------------------------------------------------------------------------
  @contextmanager
  def status(self, msg, field=0):
    self.statusbar.PushStatusText(msg, number=field)
    try:
      yield
    finally:
      self.statusbar.PopStatusText(number=field)

  #----------------------------------------------------------------------------
  def renderEntries(self):
    if len(self.app.engine.profiles) <= 0:
      return
    self.elview.SetObjects([])
    if self.app.pid is not None:
      profiles = [self.app.pid]
      self.elcols = self.elocols
    else:
      profiles = self.app.engine.profiles.keys()
      self.elcols = [self.elpcol] + self.elocols
    self.elview.SetColumns(self.elcols)
    for pid in profiles:
      profile = self.app.engine.getProfile(pid)
      for entry in profile.find():
        self.addEntry(model.Entry(pid=pid, **entry.asdict()))
    # note: this *should* be redundant, but under certain conditions
    # OLV does not work /quite/ right... so forcing a re-size.
    self.elview.AutoSizeColumns()
    # todo: wx.EVT_LIST_ITEM_DESELECTED should really make this redundant...
    self.updateToolbarTools()
    return self

  #----------------------------------------------------------------------------
  def addEntry(self, entry):
    entry.on('change', self.entryChanged)
    self.elview.AddObject(entry)

  #----------------------------------------------------------------------------
  def entryChanged(self, event):
    # TODO: there had been a terrible typo here... for some reason, wx
    #       completely squelched that. figure out how to raise that up a bit.
    # TODO: spawn this off into a different thread.
    #       ==> NOTE that means that i need to then track `dirty` state...
    self.app.engine.getProfile(event.target.pid).modify(
      event.target.id, **{event.key: event.value})

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
