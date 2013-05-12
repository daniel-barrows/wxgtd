# -*- coding: utf-8 -*-
""" Edit task dialog.

TODO: wydzielenie cześci wspólnej z dlg_checklistitem

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import logging
import datetime
import gettext
import time

import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.model import logic
from wxgtd.lib import datetimeutils as DTU
from wxgtd.wxtools.validators import Validator, ValidatorDv
from wxgtd.wxtools.validators import v_length as LVALID

from ._base_dialog import BaseDialog
from .dlg_datetime import DlgDateTime
from .dlg_remind_settings import DlgRemindSettings
from .dlg_show_settings import DlgShowSettings
from .dlg_repeat_settings import DlgRepeatSettings
from .dlg_select_tags import DlgSelectTags
from . import _fmt as fmt

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgTask(BaseDialog):
	""" Edit task dialog.

	WARRNING: non-modal dialog

	Args:
		parent: parent windows
		task_uuid: uuid task to edit; if none create new task
		parent_uuid: optional uuid of parent task
		task_type: optional task type to create
	"""

	def __init__(self, parent, task_uuid, parent_uuid=None, task_type=None):
		BaseDialog.__init__(self, parent, 'dlg_task')
		self._setup_comboboxes()
		self._setup(task_uuid, parent_uuid, task_type)
		self._refresh_static_texts()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)
		self['btn_due_date_set'].Bind(wx.EVT_BUTTON, self._on_btn_due_date_set)
		self['btn_start_date_set'].Bind(wx.EVT_BUTTON, self._on_btn_start_date_set)
		self['lb_notes_list'].Bind(wx.EVT_LISTBOX, self._on_lb_notes_list)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_btn_new_note, id=wx.ID_ADD)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_btn_delete, id=wx.ID_DELETE)
		self['btn_del_note'].Bind(wx.EVT_BUTTON, self._on_btn_del_note)
		self['btn_save_note'].Bind(wx.EVT_BUTTON, self._on_btn_save_note)
		self['btn_remind_set'].Bind(wx.EVT_BUTTON, self._on_btn_remiand_set)
		self['btn_hide_until_set'].Bind(wx.EVT_BUTTON, self._on_btn_hide_until_set)
		self['btn_repeat_set'].Bind(wx.EVT_BUTTON, self._on_btn_repeat_set)
		self['btn_select_tags'].Bind(wx.EVT_BUTTON, self._on_btn_select_tags)
		self['sl_priority'].Bind(wx.EVT_SCROLL, self._on_sl_priority)

	def _setup(self, task_uuid, parent_uuid, task_type):
		_LOG.debug("DlgTask(%r)", (task_uuid, parent_uuid, task_type))
		self._current_note = None
		self._session = OBJ.Session()
		if task_uuid:
			self._task = self._session.query(OBJ.Task).filter_by(
					uuid=task_uuid).first()
		else:
			self._task = OBJ.Task(parent_uuid=parent_uuid, priority=0,
					type=(task_type or enums.TYPE_TASK))
			logic.update_task_from_parent(self._task, parent_uuid, self._session,
					self._appconfig)
			self._session.add(self._task)
		_LOG.debug("Task=%r", self._task)
		self[wx.ID_DELETE].Enable(bool(task_uuid))
		task = self._task
		self._data = {'prev_completed': task.completed}
		self._data['duration_d'] = self._data['duration_h'] = \
				self._data['duration_m'] = 0
		if task.duration:
			duration = task.duration
			self._data['duration_d'] = int(duration / 1440)
			duration = duration % 1440
			self._data['duration_h'] = int(duration / 60)
			self._data['duration_m'] = duration % 60
		#self._data['due_time'] = self._data['due_date'] = task.due_date
		#self._data['start_time'] = self._data['start_date'] = task.start_date
		self['tc_title'].SetValidator(Validator(task, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['tc_note'].SetValidator(Validator(task, 'note',))
		self['cb_status'].SetValidator(ValidatorDv(task, 'status'))
		self['cb_context'].SetValidator(ValidatorDv(task, 'context_uuid'))
		self['cb_folder'].SetValidator(ValidatorDv(task, 'folder_uuid'))
		self['cb_goal'].SetValidator(ValidatorDv(task, 'goal_uuid'))
		self['cb_type'].SetValidator(ValidatorDv(task, 'type'))
		# parent == projekt/lista
		self['cb_project'].SetValidator(ValidatorDv(task,
				'parent_uuid'))
		self['l_created'].SetLabel(fmt.format_timestamp(task.created, True))
		self['l_modified'].SetLabel(fmt.format_timestamp(task.modified, True))
		self['cb_completed'].SetValidator(Validator(task, 'task_completed'))
		self['cb_starred'].SetValidator(Validator(task, 'starred'))
		self['sl_priority'].SetValidator(Validator(task, 'priority'))
		self['sc_duration_d'].SetValidator(Validator(self._data, 'duration_d'))
		self['sc_duration_h'].SetValidator(Validator(self._data, 'duration_h'))
		self['sc_duration_m'].SetValidator(Validator(self._data, 'duration_m'))
		# lock type change if there are subtasks
		if task_uuid and self._task.child_count > 0:
			self['cb_type'].Enable(False)

	def _setup_comboboxes(self):
		cb_status = self['cb_status']
		for key, status in sorted(enums.STATUSES.iteritems()):
			cb_status.Append(status, key)
		cb_types = self['cb_type']
		for key, typename in sorted(enums.TYPES.iteritems()):
			if key != enums.TYPE_CHECKLIST_ITEM:
				# nie można utworzyć checklist item bez checlisty jako parenta
				cb_types.Append(typename, key)
		cb_context = self['cb_context']
		for context in OBJ.Context.all():
			cb_context.Append(context.title, context.uuid)
		cb_folder = self['cb_folder']
		for folder in OBJ.Folder.all():
			cb_folder.Append(folder.title, folder.uuid)
		cb_goal = self['cb_goal']
		for goal in OBJ.Goal.all():
			cb_goal.Append(goal.title, goal.uuid)
		cb_project = self['cb_project']
		for project in OBJ.Task.all_projects():
			# projects
			cb_project.Append(project.title, project.uuid)

	def _on_save(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._task.duration = self._data['duration_d'] * 1440 + \
				self._data['duration_h'] * 60 + self._data['duration_m']
		if not self._data['prev_completed'] and self._task.completed:
			# zakonczono zadanie
			if not logic.complete_task(self._task, self._wnd, self._session):
				return
		self._session.commit()
		Publisher.sendMessage('task.update', data={'task_uuid': self._task.uuid})
		self._on_ok(evt)

	def _on_btn_due_date_set(self, _evt):
		self._set_date('due_date', 'due_time_set')

	def _on_btn_start_date_set(self, _evt):
		self._set_date('start_date', 'start_time_set')

	def _on_lb_notes_list(self, evt):
		note_uuid = evt.GetClientData()
		for note in self._task.notes:
			if note.uuid == note_uuid:
				# czy aktualne jest zmienione
				if note != self._current_note and self._current_note:
					# TODO: potwierdzenie zapisania
					value = self['tc_notes_note'].GetValue()
					if value != self._current_note.title:
						self._current_note.title = value
				self._current_note = note
				self['tc_notes_note'].SetValue(note.title or '')

	def _on_btn_new_note(self, _evt):
		self._save_current_note()
		self._current_note = OBJ.Tasknote(title=_("New note"))
		self['tc_notes_note'].SetValue(self._current_note.title)

	def _on_btn_del_note(self, _evt):
		lb_notes_list = self['lb_notes_list']
		sel = lb_notes_list.GetSelection()
		if sel < 0:
			return
		del self._task.notes[sel]
		self._refresh_static_texts()

	def _on_btn_save_note(self, _evt):
		self._save_current_note()

	def _on_btn_remiand_set(self, _evt):
		task = self._task
		alarm = None
		if task.alarm:
			task_alarm = DTU.datetime_utc2local(task.alarm)
			alarm = time.mktime(task_alarm.timetuple())
		dlg = DlgRemindSettings(self._wnd, alarm, task.alarm_pattern)
		if dlg.run(True):
			if dlg.alarm:
				task.alarm = DTU.datetime_local2utc(
						datetime.datetime.fromtimestamp(dlg.alarm))
				task.alarm_pattern = None
			else:
				task.alarm = None
				task.alarm_pattern = dlg.alarm_pattern
			logic.update_task_alarm(task)
			self._refresh_static_texts()

	def _on_btn_hide_until_set(self, _evt):
		task = self._task
		date_time = None
		if task.hide_until:
			task_hide_until = DTU.datetime_utc2local(task.hide_until)
			date_time = time.mktime(task_hide_until.timetuple())
		dlg = DlgShowSettings(self._wnd, date_time, task.hide_pattern)
		if dlg.run(True):
			if dlg.datetime:
				task.hide_until = DTU.datetime_local2utc(
						datetime.datetime.fromtimestamp(dlg.datetime))
				task.hide_pattern = 'given date'
			else:
				task.hide_until = None
			task.hide_pattern = dlg.pattern
			logic.update_task_hide(task)
			self._refresh_static_texts()

	def _on_btn_repeat_set(self, _evt):
		task = self._task
		dlg = DlgRepeatSettings(self._wnd, task.repeat_pattern, task.repeat_from)
		if dlg.run(True):
			task.repeat_from = dlg.repeat_from
			task.repeat_pattern = dlg.pattern
			self._refresh_static_texts()

	def _on_btn_select_tags(self, _evt):
		task = self._task
		tags_uuids = [tasktag.tag_uuid for tasktag in task.tags]
		dlg = DlgSelectTags(self._wnd, tags_uuids)
		if dlg.run(True):
			new_tags = dlg.selected_tags
			for tasktag in list(task.tags):
				if tasktag.tag_uuid not in new_tags:
					task.tags.delete(tasktag)
				else:
					new_tags.remove(tasktag.tag_uuid)
			for tag_uuid in new_tags:
				tasktag = OBJ.TaskTag()
				tasktag.tag = self._session.query(OBJ.Tag).filter_by(
						uuid=tag_uuid).first()
				task.tags.append(tasktag)
			self._refresh_static_texts()

	def _on_btn_delete(self, _evt):
		tuuid = self._task.uuid
		if tuuid:
			if logic.delete_task(tuuid, self.wnd, self._session):
				Publisher.sendMessage('task.delete', data={'task_uuid': tuuid})
				self._on_ok(None)

	def _on_sl_priority(self, _evt):
		self['l_prio'].SetLabel(enums.PRIORITIES[self['sl_priority'].GetValue()])

	def _save_current_note(self):
		cnote = self._current_note
		if cnote:
			value = self['tc_notes_note'].GetValue()
			if value and value != cnote.title:
				cnote.title = value
				cnote.modified = datetime.datetime.utcnow()
				if not cnote.created:
					cnote.created = cnote.modified
					self._task.notes.append(cnote)
			wx.CallAfter(self._refresh_static_texts)

	def _refresh_static_texts(self):
		""" Odświeżenie pól dat na dlg """
		task = self._task
		self['l_due'].SetLabel(fmt.format_timestamp(task.due_date,
				task.due_time_set))
		self['l_start_date'].SetLabel(fmt.format_timestamp(task.start_date,
				task.start_time_set))
		self['l_tags'].SetLabel(", ".join(tag.tag.title for tag in task.tags) or '')
		if task.alarm_pattern:
			self['l_remind'].SetLabel(enums.REMIND_PATTERNS[task.alarm_pattern])
		elif task.alarm:
			self['l_remind'].SetLabel(fmt.format_timestamp(task.alarm, True))
		else:
			self['l_remind'].SetLabel('')
		if task.hide_pattern and task.hide_pattern != 'given date':
			self['l_hide_until'].SetLabel(enums.HIDE_PATTERNS[task.hide_pattern])
		elif task.hide_until:
			self['l_hide_until'].SetLabel(fmt.format_timestamp(task.hide_until,
					True))
		else:
			self['l_hide_until'].SetLabel('')
		self['l_repeat'].SetLabel(enums.REPEAT_PATTERN.get(task.repeat_pattern,
				task.repeat_pattern or ""))
		lb_notes_list = self['lb_notes_list']
		lb_notes_list.Clear()
		for note in task.notes:
			lb_notes_list.Append(note.title[:50], note.uuid)
		self['l_prio'].SetLabel(enums.PRIORITIES[task.priority])
		if task.completed:
			self['l_completed_date'].SetLabel(fmt.format_timestamp(task.completed,
					True))
		else:
			self['l_completed_date'].SetLabel('')

	def _set_date(self, attr_date, attr_time_set):
		""" Wyśweitlenie dlg wyboru daty dla danego atrybutu """
		value = getattr(self._task, attr_date)
		if value:
			value = DTU.datetime_utc2local(value)
			value = time.mktime(value.timetuple())
		dlg = DlgDateTime(self._wnd, value,
				getattr(self._task, attr_time_set))
		if dlg.run(True):
			date = None
			if dlg.timestamp:
				date = datetime.datetime.fromtimestamp(dlg.timestamp)
				date = DTU.datetime_local2utc(date)
			setattr(self._task, attr_date, date)
			setattr(self._task, attr_time_set, dlg.is_time_set)
			self._refresh_static_texts()
