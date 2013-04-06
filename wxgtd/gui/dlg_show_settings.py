# -*- coding: utf-8 -*-

""" Klasa bazowa dla wszystkich dlg.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import logging

import wx

from wxgtd.wxtools.validators import ValidatorDate, ValidatorTime
from wxgtd.model import enums

from _base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgShowSettings(BaseDialog):
	""" Dlg wyboru ustawień dot. wyświetlania zadania
	"""

	def __init__(self, parent, date, pattern):
		""" Konst
		parent - okno nadrzędne
		date - czas jako long
		pattern - opis przpomnienia (z enums.HIDE_PATTERNS)
		"""
		self._data = {'date': None, 'time': None, 'pattern': pattern,
				'datetime': date}
		BaseDialog.__init__(self, parent, 'dlg_show_settings')
		self._setup(date, pattern)

	@property
	def datetime(self):
		return self._data['datetime']

	@property
	def pattern(self):
		return self._data['pattern']

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

		self['dp_date'].SetValidator(ValidatorDate(self._data, 'date'))
		self['tc_time'].SetValidator(ValidatorTime(self._data, 'time'))

		c_pattern = self['c_pattern']
		for rem_key, rem_name in enums.HIDE_PATTERNS_LIST:
			c_pattern.Append(rem_name, rem_key)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)

	def _setup(self, date, pattern):
		_LOG.debug("DlgShowSettings(%r)", (date, pattern))
		self['rb_always'].SetValue(True)
		if date:
			self._data['date'] = self._data['time'] = date
			if not pattern:
				self['rb_datetime'].SetValue(True)
				return
		if pattern:
			c_pattern = self['c_pattern']
			for idx in xrange(c_pattern.GetCount()):
				if c_pattern.GetClientData(idx) == pattern:
					c_pattern.Select(idx)
					self['rb_before'].SetValue(True)
					return

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		if self['rb_always'].GetValue():
			self._data['pattern'] = self._data['datetime'] = None
		elif self['rb_datetime'].GetValue():
			self._data['datetime'] = self._data['date'] + self._data['time']
			self._data['pattern'] = None
		else:
			self._data['datetime'] = None
			c_pattern = self['c_pattern']
			self._data['pattern'] = c_pattern.GetClientData(
					c_pattern.GetSelection())
		BaseDialog._on_ok(self, evt)