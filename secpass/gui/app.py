# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/28
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import sys, os.path, logging, argparse, ConfigParser, pkg_resources
from contextlib import contextmanager
import wx
from wx import xrc, wizard
from wx.lib.wordwrap import wordwrap
import wx.lib.mixins.listctrl as listmix
import ObjectListView as OLV

from secpass import engine, api, model, util
from secpass.util import resolvePath, asbool, adict
from secpass.adict import adict

# todo: make the status line display the number of selected and/or
#       unselected entries

# todo: how to make an exception open in a window instead of showing
#       on console?...
#       or does wx already take care of that, ie. on windows, it uses a dialog
#       since there is no console?

# todo: remember column sorting preference...

#------------------------------------------------------------------------------
log = logging.getLogger(__name__)
rootlog = logging.getLogger()
rootlog.setLevel(logging.WARNING)
rootlog.addHandler(logging.StreamHandler())
# TODO: add a logging formatter...

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
class SecPassGui(wx.App):

  #----------------------------------------------------------------------------
  def __init__(self, config=None, profile=None, *args, **kw):
    self.pidwid   = dict()
    self.widpid   = dict()
    self.curpid   = profile or None
    self.config   = config or None
    self.engine   = engine.Engine(self.config)

    # TODO: remove this...
    print 'TODO: remove this force-profile-to-"test"...'
    self.curpid = 'test'

    try:
      self.engine.getProfile(self.curpid)
    except KeyError:
      # todo: display error and switch to default profile...
      raise ValueError('Profile "%s" not found' % (self.curpid,))

    # copy 'gui' and 'common' sections into the config if missing
    # todo: should this be in `secpass.engine`?...
    for section in ('common', 'gui'):
      if section not in self.engine.config.sections():
        defcfg = ConfigParser.RawConfigParser()
        defcfg.optionxform = str
        defcfg.readfp(pkg_resources.resource_stream('secpass', 'res/config.ini'))
        self.engine.config.add_section(section)
        for key, val in defcfg.items(section):
          if defcfg.has_option('DEFAULT', key) and defcfg.get('DEFAULT', key) == val:
            continue
          self.engine.config.set(section, key, val)
    self.combined = asbool(self.engine.config.get('gui', 'combined'))
    if self.curpid is None and not self.combined:
      self.curpid = self.engine.config.get('DEFAULT', 'profile.default')
    super(SecPassGui, self).__init__(*args, **kw)

  #----------------------------------------------------------------------------
  def OnInit(self):
    # todo: convert to using pkg_resources...
    #         self.wxres = wx.xrc.EmptyXmlResource()
    #         self.wxres.LoadFromString( ...load... )
    #       *but*... how does loading of images, etc work?
    self.wxres = xrc.XmlResource(
      os.path.join(os.path.dirname(__file__), 'res', 'wx.xrc'))
    self.createFrame()
    self.update()
    if len(self.engine.profiles) <= 0:
      self.openProfileWizard()
      # TODO: set the engine to the new profile...
    self.renderEntries()
    return True

  #----------------------------------------------------------------------------
  def getConfig(self, section, name, default=None):
    if not self.engine.config.has_option(section, name):
      return default
    return self.engine.config.get(section, name)

  #----------------------------------------------------------------------------
  def createFrame(self):
    self.frame     = self.wxres.LoadFrame(None, 'window.main')
    self.toolbar   = xrc.XRCCTRL(self.frame, 'toolbar')
    self.statusbar = xrc.XRCCTRL(self.frame, 'statusbar')
    self.menubar   = self.frame.GetMenuBar()
    self.filter    = None
    self.profmenu  = None
    self.tools     = adict(
      create = self.toolbar.FindById(xrc.XRCID('tool.create')),
      edit   = self.toolbar.FindById(xrc.XRCID('tool.update')),
      rotate = self.toolbar.FindById(xrc.XRCID('tool.rotate')),
      clip   = self.toolbar.FindById(xrc.XRCID('tool.copy')),
      delete = self.toolbar.FindById(xrc.XRCID('tool.delete')),
      )
    self.frame.Bind(wx.EVT_MENU, self.OnQuit, id=wx.ID_EXIT)
    self.frame.Bind(wx.EVT_MENU, self.OnHelp, id=wx.ID_HELP)
    self.frame.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
    self.frame.Bind(wx.EVT_MENU, self.OnPreferences, id=wx.ID_PREFERENCES)
    self.frame.Bind(wx.EVT_MENU, self.OnCheckUpdate, id=xrc.XRCID('menuitem.updatecheck'))
    self.frame.Bind(wx.EVT_MENU, self.OnProfileCreate, id=xrc.XRCID('menuitem.profile-create'))
    self.frame.Bind(wx.EVT_TEXT, self.OnFilterChange, id=xrc.XRCID('input.filter'))
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntryCreate, id=self.tools.create.Id)
    self.toolbar.Bind(wx.EVT_TOOL, self.OnEntriesDelete, id=self.tools.delete.Id)

    # todo: find out why the 'about' menuitem doesn't use the standard icon...
    # todo: load window size from preferences...
    # ensure that the window is at least 600x400
    cur = self.frame.GetSize()
    cur.width  = int(self.getConfig('gui', 'main.width', 600))
    cur.height = int(self.getConfig('gui', 'main.height', 400))
    self.frame.SetSize(cur)
    self.SetTopWindow(self.frame)

    # setup the ObjectListView to actually show the entries
    # todo: much of this should be moved into the XRC...
    self.elbox = xrc.XRCCTRL(self.frame, 'box.entries')
    self.elview = OLV.ObjectListView(
      self.elbox, wx.ID_ANY, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
    self.elview.oddRowsBackColor  = self.getConfig('gui', 'main.rowcolor.odd', '#fcfcfc')
    self.elview.evenRowsBackColor = self.getConfig('gui', 'main.rowcolor.even', '#dedede')
    self.elview.cellEditMode      = OLV.ObjectListView.CELLEDIT_DOUBLECLICK
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.elview, 1, wx.ALL|wx.EXPAND, 0)
    self.elbox.SetSizer(sizer)
    # todo: i18n...
    self.elpcol = OLV.ColumnDefn('Profile', 
                                 valueGetter=self.getEntryProfileName,
                                 minimumWidth=10, isSpaceFilling=True)
    self.elocols = [
      OLV.ColumnDefn('Service',  valueGetter='service',  minimumWidth=10, isSpaceFilling=True),
      OLV.ColumnDefn('Role',     valueGetter='role',     minimumWidth=10, isSpaceFilling=True),
      OLV.ColumnDefn('Password', valueGetter='password', minimumWidth=10, isSpaceFilling=True),
      OLV.ColumnDefn('Notes',    valueGetter='notes',    minimumWidth=10, isSpaceFilling=True,
                     #cellEditorCreator=self.notesEditor
                     ),
      ]
    self.elcols = [self.elpcol] + self.elocols
    self.elview.SetColumns(self.elcols)
    self.elview.SetEmptyListMsg('No entries to display.')
    self.elview.SetObjects([])

    self.elview.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnCheckSelection)
    self.elview.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnCheckSelection)

    self.frame.Show()

  #----------------------------------------------------------------------------
  def getEntryProfileName(self, entry):
    return self.engine.getProfile(entry.pid).name

  #----------------------------------------------------------------------------
  def notesEditor(self, olv, rowIndex, subItemIndex):
    return NotesEditor(olv, rowIndex, subItemIndex)

  #----------------------------------------------------------------------------
  def update(self):
    for tool in self.tools.values():
      self.toolbar.EnableTool(tool.Id, False)
    if len(self.engine.profiles) > 0:
      self.toolbar.EnableTool(self.tools.create.Id, True)
      # TODO: if any entries are selected:
      # for tool in self.tools.values():
      #   self.toolbar.EnableTool(tool.Id, True)
    self.updateProfileMenu()

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
    pmenu.AppendCheckItem(self.pidwid[None], 'All profiles combined',
                          'Manage entries in all profiles')
    pmenu.Bind(wx.EVT_MENU, self.OnProfileSwitch, id=self.pidwid[None])
    pmenu.AppendSeparator()
    def cmpprof(a, b):
      return cmp(a.name, b.name)
    for profile in sorted(self.engine.profiles.values(), cmp=cmpprof):
      self.pidwid[profile.id] = wx.NewId()
      # todo: i18n...
      pmenu.AppendCheckItem(self.pidwid[profile.id], profile.name,
                            'Manage entries in the "%s" profile' % (profile.name,))
      pmenu.Bind(wx.EVT_MENU, self.OnProfileSwitch, id=self.pidwid[profile.id])
    pmenu.Check(self.pidwid[self.curpid], True)
    self.widpid = dict([[w, p] for p, w in self.pidwid.items()])

  #----------------------------------------------------------------------------
  def NIY(self, func):
    # TODO: remove this
    wx.MessageBox(func + ' not implemented yet.', 'Error', wx.OK|wx.ICON_ERROR)

  #----------------------------------------------------------------------------
  def OnCheckUpdate(self, e):
    # TODO: implement
    self.NIY('Update checking')

  #----------------------------------------------------------------------------
  def OnPreferences(self, e):
    # TODO: implement
    self.NIY('Preferences')

  #----------------------------------------------------------------------------
  def OnHelp(self, e):
    # todo: get the homepage url from setup.py...
    url = 'http://github.com/metagriffin/secpass'
    if not wx.LaunchDefaultBrowser(url):
      # todo: i18n...
      wx.MessageBox('Your browser could not be launched - please'
                    ' go to "%s" manually to get secpass help content.' % (url,))

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
    self.OnCheckSelection()
    return self

  #----------------------------------------------------------------------------
  def OnProfileCreate(self, e):
    self.openProfileWizard()

  #----------------------------------------------------------------------------
  def OnEntryCreate(self, e):
    with self.status(self._('Creating new entry...')):
      if self.curpid is None:
        # TODO: implement
        raise TypeError('CURPID IS NONE!')
      self.entryCreate(self.curpid)

  #----------------------------------------------------------------------------
  def entryCreate(self, pid):
    # todo: i18n...
    profile = self.engine.getProfile(pid)
    entry = model.Entry(pid=pid, **profile.create(api.Entry(
      service  = 'New service',
      role     = 'New role',
      password = util.generatePassword(profile.settings))).asdict())
    self.elview.AddObject(entry)
    self.elview.SelectObject(entry, deselectOthers=True, ensureVisible=True)
    self.elview.StartCellEdit(self.elview.GetIndexOf(entry),
                              1 if self.elcols[0] is self.elpcol else 0)

  #----------------------------------------------------------------------------
  def OnEntriesDelete(self, e):
    # TODO: open a 'confirm' message box...
    with self.status(self._('Deleting entries...')):
      entries = self.elview.GetSelectedObjects()
      for entry in entries:
        self.engine.getProfile(entry.pid).delete(entry.id)
        self.elview.RemoveObject(entry)
    # todo: wx.EVT_LIST_ITEM_DESELECTED should really make this redundant...
    self.OnCheckSelection()

  #----------------------------------------------------------------------------
  def OnCheckSelection(self, e=None):
    sel = len(self.elview.GetSelectedObjects())
    self.toolbar.EnableTool(self.tools.delete.Id, sel > 0)
    self.toolbar.EnableTool(self.tools.rotate.Id, sel > 0)
    self.toolbar.EnableTool(self.tools.edit.Id, sel == 1)
    self.toolbar.EnableTool(self.tools.clip.Id, sel == 1)

  #----------------------------------------------------------------------------
  def OnProfileSwitch(self, e):
    if e.GetEventType() != wx.wxEVT_COMMAND_MENU_SELECTED:
      return
    if e.Id not in self.widpid:
      # todo: more detail / log error ...
      return wx.MessageBox('Internal error: unexpected WID %r' % (e.Id,))
    self.curpid = self.widpid[e.GetId()]
    if self.curpid is not None:
      # todo: i18n...
      profname = self.engine.profiles[self.curpid].name
      status = 'Switching to "%s" profile...' % (profname,)
    else:
      # todo: i18n...
      status = 'Switching to all profiles combined...'
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
    # if self.engine.settings is None:
    #   return
    self.elview.SetObjects([])
    if self.curpid is not None:
      profiles = [self.curpid]
      self.elcols = self.elocols
    else:
      profiles = self.engine.profiles.keys()
      self.elcols = [self.elpcol] + self.elocols
    self.elview.SetColumns(self.elcols)
    for pid in profiles:
      profile = self.engine.getProfile(pid)
      for entry in profile.find():
        self.elview.AddObject(model.Entry(pid=pid, **entry.asdict()))
    # note: this *should* be redundant, but under certain conditions
    # OLV does not work /quite/ right... so forcing a re-size.
    self.elview.AutoSizeColumns()
    # todo: wx.EVT_LIST_ITEM_DESELECTED should really make this redundant...
    self.OnCheckSelection()
    return self

  #----------------------------------------------------------------------------
  def openProfileWizard(self):
    # todo: check self.config.settings to see if this is the first
    # profile, and if so, add a little more explanation...
    wizard = self.wxres.LoadObject(None, 'wizard.profile', 'wxWizard')
    initpg = wx.xrc.XRCCTRL(wizard, 'wizardpage.generic')
    wizard.RunWizard(initpg)
    wizard.Destroy()

  #----------------------------------------------------------------------------
  def OnQuit(self, e):
    # TODO: save settings... eg [gui] main.*, etc.
    # wx.MessageBox('Your name is %s %s!' %
    #               (self.text1.GetValue(), self.text2.GetValue()), 'Feedback')
    self.frame.Close()

  #----------------------------------------------------------------------------
  def OnAbout(self, e):
    # todo: any way to get the url, copyright, description, etc from
    #       setup.py (beyond just the version)?...
    # todo: i18n...
    pkg = pkg_resources.require('secpass')[0]
    info = wx.AboutDialogInfo()
    info.Name        = 'Secure Passwords'
    info.Version     = pkg.version
    info.Copyright   = 'Copyright (C) 2013-EOT metagriffin'
    info.Description = wordwrap(
      'Helping you very securely manage very secure credentials since 2013'
      ' (street cred optional).',
      350, wx.ClientDC(self.frame)) \
      + '\n\n' \
      + 'secpass/' + info.Version + '\n' \
      + 'ObjectListView/' + OLV.__version__ + '\n' \
      + 'wxPython/' + wx.VERSION_STRING + '\n' \
      + 'Python/' + sys.version.split()[0] + '\n'
    info.WebSite     = ('http://github.com/metagriffin/secpass',
                        'Official Website')
    info.Developers  = ('metagriffin <metagriffin@uberdev.org>',)
    info.Artists     = ('metagriffin <metagriffin@uberdev.org>',)
    # todo: how to fetch this using pkg_resources?...
    # todo: use a better re-formatting system...
    text = open(
      os.path.join(os.path.dirname(__file__), '..', '..', 'LICENSE.txt'),
      'rb').read()
    text = text.replace('\n\n', '[REALNEWLINEREALNEWLINEREALNEWLINE]')
    text = text.replace('\n', ' ')
    text = text.replace('[REALNEWLINEREALNEWLINEREALNEWLINE]', '\n\n')
    info.License     = wordwrap(text, 350,wx.ClientDC(self.frame))
    wx.AboutBox(info)

  #----------------------------------------------------------------------------
  def _(self, message):
    # TODO: i18n...
    return message

#------------------------------------------------------------------------------
def main(argv=None):

  defconf = os.environ.get('SECPASS_CONFIG', api.DEFAULT_CONFIG)

  cli = argparse.ArgumentParser(
    description = 'Secure Passwords Graphical User Interfale',
    )

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
    help='configuration profile id or name (defaults to configuration)')

  options = cli.parse_args(args=argv)

  if options.verbose == 1:
    rootlog.setLevel(logging.INFO)
  elif options.verbose > 1:
    rootlog.setLevel(logging.DEBUG)

  options.config = resolvePath(options.config)

  gui = SecPassGui(config=options.config, profile=options.profile)
  gui.MainLoop()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
