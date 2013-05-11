# -*- coding: utf-8 -*-
""" Preferences dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import os
import logging
import gettext

import wx

from wxgtd.wxtools.validators import Validator
from wxgtd.model import enums
from wxgtd.lib.appconfig import AppConfig

from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class AppConfigWrapper(object):
	""" Wrapper for AppConfig class that allow use it with validators. """

	def __init__(self):
		self._config = AppConfig()

	def __getitem__(self, key):
		key = key.split('/')
		return self._config.get(key[0], key[1])

	def __setitem__(self, key, value):
		key = key.split('/')
		self._config.set(key[0], key[1], value)

	def get(self, key, default=None):
		key = key.split('/')
		return self._config.get(key[0], key[1], default)


class DlgPreferences(BaseDialog):
	""" Preferences dialog.

	Args:
		parent: parent window
	"""

	def __init__(self, parent):
		BaseDialog.__init__(self, parent, 'dlg_preferences', save_pos=False)
		self._setup()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)

		config = self._config = AppConfigWrapper()

		self['sc_hotlist_due'].SetValidator(Validator(config, 'hotlist/due'))
		self['sl_hotlist_priority'].SetValidator(Validator(config,
				'hotlist/priority'))
		self['cb_hotlist_starred'].SetValidator(Validator(config,
				'hotlist/starred'))
		self['cb_hotlist_next_action'].SetValidator(Validator(config,
				'hotlist/next_action'))
		self['cb_hotlist_started'].SetValidator(Validator(config,
				'hotlist/starred'))
		self['cb_hotlist_started'].SetValidator(Validator(config,
				'hotlist/started'))
		self['tc_sync_filename'].SetValidator(Validator(config,
				'files/last_sync_file'))
		self._on_sl_priority(None)
		self['cb_sync_on_startup'].SetValidator(Validator(config,
				'sync/sync_on_startup'))
		self['cb_sync_on_exit'].SetValidator(Validator(config,
				'sync/sync_on_exit'))
		cond_or = config.get('hotlist/condition_or', True)
		self['rb_hotlist_cond_or'].SetValue(cond_or)
		self['rb_hotlist_cond_and'].SetValue(not cond_or)
		# task
		# # inheritance from project
		self['cb_tasks_inh_context'].SetValidator(Validator(config,
				'task/inerit_context'))
		self['cb_tasks_inh_goal'].SetValidator(Validator(config,
				'task/inerit_goal'))
		self['cb_tasks_inh_folder'].SetValidator(Validator(config,
				'task/inerit_folder'))
		self['cb_tasks_inh_tags'].SetValidator(Validator(config,
				'task/inerit_tags'))
		self['cb_notif_popup_reminds'].SetValidator(Validator(config,
				'notification/popup_alarms'))

	def _create_bindings(self):
		BaseDialog._create_bindings(self)
		self['sl_hotlist_priority'].Bind(wx.EVT_SCROLL, self._on_sl_priority)
		self['btn_sync_file_select'].Bind(wx.EVT_BUTTON,
				self._on_btn_sync_file_select)

	def _setup(self):
		_LOG.debug("DlgPreferences()")

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._config['hotlist/condition_or'] = self['rb_hotlist_cond_or'].GetValue()
		BaseDialog._on_ok(self, evt)

	def _on_sl_priority(self, _evt):
		self['l_hotlist_priority'].SetLabel(
				enums.PRIORITIES[self['sl_hotlist_priority'].GetValue()])

	def _on_btn_sync_file_select(self, _evt):
		last_file = self['tc_sync_filename'].GetValue()
		if not last_file:
			last_file = os.path.expanduser('~/')
		dlg = wx.FileDialog(self._wnd,
				_("Please select sync file."),
				defaultDir=os.path.dirname(last_file),
				defaultFile=last_file,
				style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			self['tc_sync_filename'].SetValue(dlg.GetPath())
		dlg.Destroy()
