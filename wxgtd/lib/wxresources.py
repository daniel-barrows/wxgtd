# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904, C0103
""" Utilities for wx resources.

Copyright (c) Karol Będkowski, 2004-2013

This file is part of wxGTD
Licence: GPLv2+
"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2004-2013"
__version__ = "2013-04-27"

import re
import locale
import gettext

from wx import xrc
from wx.lib import masked
from wx.lib import colourselect as csel

from .appconfig import AppConfig

_ = gettext.gettext


def _localize(match_object):
	""" Replace strings by it localized version. """
	return ''.join((match_object.group(1), _(match_object.group(2)),
			match_object.group(3)))


class NumCtrlXmlHandler(xrc.XmlResourceHandler):
	""" Custom control: "NumCtrl". """

	def __init__(self):
		xrc.XmlResourceHandler.__init__(self)
		self.AddWindowStyles()

	def CanHandle(self, node):
		return self.IsOfClass(node, "NumCtrl")

	def DoCreateResource(self):
		fractionWidth = int(self.GetParamValue('fractionWidth')) \
				if self.HasParam('fractionWidth') else 2
		integerWidth = int(self.GetParamValue('integerWidth')) \
				if self.HasParam('integerWidth') else 2
		ctrl = masked.NumCtrl(
				self.GetParentAsWindow(),
				self.GetID(),
				allowNegative=False,
				fractionWidth=fractionWidth,
				integerWidth=integerWidth,
				groupChar=' ',
				allowNone=True,
				decimalChar=locale.localeconv()['decimal_point'],)
		self.SetupWindow(ctrl)
		self.CreateChildren(ctrl)
		return ctrl


class TimeCtrlXmlHandler(xrc.XmlResourceHandler):
	""" Custom control: "TimeCtrl". """
	def __init__(self):
		xrc.XmlResourceHandler.__init__(self)
		self.AddWindowStyles()

	def CanHandle(self, node):
		return self.IsOfClass(node, "TimeCtrl")

	def DoCreateResource(self):
		ctrl = masked.TimeCtrl(
				self.GetParentAsWindow(),
				self.GetID(),
				display_seconds=True,
				fmt24hr=True)
		self.SetupWindow(ctrl)
		self.CreateChildren(ctrl)
		return ctrl


class ColourSelectHandler(xrc.XmlResourceHandler):
	""" Custom control: "ColourSelect". """
	def __init__(self):
		xrc.XmlResourceHandler.__init__(self)
		self.AddWindowStyles()

	def CanHandle(self, node):
		return self.IsOfClass(node, "ColourSelect")

	def DoCreateResource(self):
		ctrl = csel.ColourSelect(
				self.GetParentAsWindow(),
				self.GetID(),
				size=self.GetSize())
		self.SetupWindow(ctrl)
		self.CreateChildren(ctrl)
		return ctrl


_XRC_CACHE = {}


def load_xrc_resource(filename):
	""" Load resources from xrc file, localize it and handle custom controls.

	Resources are cached.

	Args:
		filename: path to xrc resource file

	Returns:
		wxc resource object.
	"""
	xrcfile_path = AppConfig().get_data_file(filename)
	res = _XRC_CACHE.get(xrcfile_path)
	if res is None:
		with open(xrcfile_path) as xrc_file:
			data = xrc_file.read()
		data = data.decode('UTF-8')
		re_gettext = re.compile(r'(\<label\>)(.*?)(\<\/label\>)')
		data = re_gettext.sub(_localize, data)
		re_gettext = re.compile(r'(\<title\>)(.*?)(\<\/title\>)')
		data = re_gettext.sub(_localize, data)
		re_gettext = re.compile(r'(\<tooltip\>)(.*?)(\<\/tooltip\>)')
		data = re_gettext.sub(_localize, data)
		data = data.encode('UTF-8')
		res = xrc.EmptyXmlResource()
		res.InsertHandler(NumCtrlXmlHandler())
		res.InsertHandler(TimeCtrlXmlHandler())
		res.InsertHandler(ColourSelectHandler())
		res.LoadFromString(data)
		_XRC_CACHE[xrcfile_path] = res
	return res
