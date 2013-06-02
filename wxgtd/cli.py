# -*- coding: utf-8 -*-
""" Main module - cli interface

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-01"


import os
import gettext
import locale
import optparse
import logging

import sys
reload(sys)
try:
	sys.setappdefaultencoding("utf-8")  # pylint: disable=E1101
except AttributeError:
	sys.setdefaultencoding("utf-8")  # pylint: disable=E1101


_LOG = logging.getLogger(__name__)


from wxgtd import version
from wxgtd.model import queries


def _parse_opt():
	""" Parse cli options. """
	optp = optparse.OptionParser(version=version.NAME + " " + version.VERSION)

	group = optparse.OptionGroup(optp, "List tasks")
	group.add_option('--tasks', '-t', action="store_const",
			const=queries.QUERY_ALL_TASK,
			dest="query_group", help='show all tasks')
	group.add_option('--hotlist', action="store_const",
			const=queries.QUERY_HOTLIST,
			dest="query_group", help='show task in hotlist')
	group.add_option('--starred', action="store_const",
			const=queries.QUERY_STARRED,
			dest="query_group", help='show starred tasks')
	group.add_option('--basket', action="store_const",
			const=queries.QUERY_BASKET,
			dest="query_group", help='show tasks in basket')
	group.add_option('--finished', action="store_const",
			const=queries.QUERY_FINISHED,
			dest="query_group", help='show finished tasks')
	group.add_option('--projects', action="store_const",
			const=queries.QUERY_PROJECTS,
			dest="query_group", help='show projects')
	group.add_option('--checklists', action="store_const",
			const=queries.QUERY_CHECKLISTS,
			dest="query_group", help='show checklists')
	group.add_option('--future-alarms', action="store_const",
			const=queries.QUERY_FUTURE_ALARMS,
			dest="query_group", help='show task with alarms in future')
	optp.add_option_group(group)

	group = optparse.OptionGroup(optp, "Task operations")
	group.add_option('--quick-task', '-q', dest="quick_task_title",
			help='add quickly task', type="string")
	optp.add_option_group(group)

	group = optparse.OptionGroup(optp, "List tasks options")
	group.add_option('--show-finished', action="store_true",
			dest="query_show_finished", help='show finished tasks')
	group.add_option('--show-subtask', action="store_true",
			dest="query_show_subtask", help='show subtasks')
	group.add_option('--dont-hide-until', action="store_true",
			dest="query_dont_hide_until", help="show hidden task")
	group.add_option('--parent', dest="parent_uuid",
			help='set parent UUID for query')
	group.add_option('--search', '-s', dest="search_text",
			help='search for title/note')
	group.add_option('--verbose', '-v', action="count",
			dest="verbose", help='show more information')
	group.add_option('--output-csv', action="store_true",
			dest="output_csv", help='show result as csv file')
	optp.add_option_group(group)

	group = optparse.OptionGroup(optp, "Debug options")
	group.add_option('--debug', '-d', action="store_true", default=False,
			help='enable debug messages')
	group.add_option('--debug-sql', action="store_true", default=False,
			help='enable sql debug messages')
	optp.add_option_group(group)
	options, args = optp.parse_args()
	if not any((options.quick_task_title, options.query_group >= 0)):
		optp.print_help()
		exit(0)
	return options, args


def _setup_locale(app_config):
	""" setup locales and gettext """
	locales_dir = app_config.locales_dir
	package_name = 'wxgtd'
	_LOG.info('run: locale dir: %s' % locales_dir)
	try:
		locale.bindtextdomain(package_name, locales_dir)
		locale.bind_textdomain_codeset(package_name, "UTF-8")
	except AttributeError:
		pass
	default_locale = locale.getdefaultlocale()
	locale.setlocale(locale.LC_ALL, '')
	os.environ['LC_ALL'] = os.environ.get('LC_ALL') or default_locale[0]
	gettext.install(package_name, localedir=locales_dir, unicode=True,
			names=("ngettext", ))
	gettext.bindtextdomain(package_name, locales_dir)
	gettext.textdomain(package_name)
	gettext.bindtextdomain('wxstd', locales_dir)
	gettext.bind_textdomain_codeset(package_name, "UTF-8")
	_LOG.info('locale: %s' % str(locale.getlocale()))


def _try_path(path):
	""" Check if in given path exists wxgtd.db file. """
	file_path = os.path.join(path, 'wxgtd.db')
	if os.path.isfile(file_path):
		return file_path
	return None


def _create_file_dir(db_filename):
	""" Create dirs for given file if not exists. """
	db_dirname = os.path.dirname(db_filename)
	if not os.path.isdir(db_dirname):
		os.mkdir(db_dirname)


def _find_db_file(config):
	""" Find existing database file. """
	db_filename = _try_path(config.main_dir)
	if not db_filename:
		db_filename = _try_path(os.path.join(config.main_dir, 'db'))
	if not db_filename:
		db_dir = os.path.join(config.main_dir, 'db')
		if os.path.isdir(db_dir):
			db_filename = os.path.join(db_dir, 'wxgtd.db')
	if not db_filename:
		db_filename = os.path.join(config.user_share_dir, 'wxgtd.db')
	return db_filename


def run():
	""" Run application. """
	# parse options
	options, args = _parse_opt()

	# app config
	from wxgtd.lib import appconfig

	# logowanie
	from wxgtd.lib.logging_setup import logging_setup
	logging_setup('wxgtd.log', options.debug, options.debug_sql)

	# konfiguracja
	config = appconfig.AppConfig('wxgtd.cfg', 'wxgtd')
	config.load_defaults(config.get_data_file('defaults.cfg'))
	config.load()
	config.debug = options.debug

	# locale
	_setup_locale(config)

	# database
	from wxgtd.model import db
	db_filename = _find_db_file(config)
	_create_file_dir(db_filename)
	# connect to databse
	db.connect(db_filename, options.debug_sql)

	if options.quick_task_title:
		from wxgtd.logic import quicktask as quicktask_logic
		quicktask_logic.create_quicktask(options.quick_task_title)
	elif options.query_group >= 0:
		_list_tasks(options, args)

	config.save()
	exit(0)


from wxgtd.gui import _fmt as fmt
from wxgtd.model import enums


def _list_tasks(options, _args):
	from wxgtd.model import objects as OBJ
	group_id = options.query_group
	query_opt = 0
	if options.query_show_finished:
		query_opt |= queries.OPT_SHOW_FINISHED
	if options.query_show_subtask:
		query_opt |= queries.OPT_SHOW_SUBTASKS
	if not options.query_dont_hide_until:
		query_opt |= queries.OPT_HIDE_UNTIL
	params = queries.build_query_params(group_id, query_opt,
			options.parent_uuid, options.search_text or '')

	tasks = OBJ.Task.select_by_filters(params)
	if options.output_csv:
		_print_csv_tasks_list(tasks, options.verbose)
	else:
		_print_simple_tasks_list(tasks, options.verbose)


def _print_simple_tasks_list(tasks, verbose):
	types = {enums.TYPE_PROJECT: 'P',
			enums.TYPE_CHECKLIST: 'C',
			enums.TYPE_CHECKLIST_ITEM: '-',
			enums.TYPE_CALL: 'c',
			enums.TYPE_RETURN_CALL: 'r',
			enums.TYPE_EMAIL: 'e',
			enums.TYPE_SMS: 's'}
	for task in tasks:
		if verbose > 0:
			print ('*' if task.starred else ' '),
			print types.get(task.type, ' '),
			print (task.priority if task.priority >= 0 else ' '),
			print (' [F] ' if task.completed else '     '),
		print '%-80s' % task.title[:80],
		print '%-19s' % fmt.format_timestamp(task.due_date, task.due_time_set),
		print '%-19s' % fmt.format_timestamp(task.start_date, task.start_time_set),
		if verbose > 0:
			flags = ("["
					+ ("r" if task.repeat_pattern else " ")
					+ ("a" if task.alarm else " ")
					+ ("n" if task.note else " ")
					+ "]")
			print flags,
		if verbose > 1:
			print task.uuid,
		print


def _print_csv_tasks_list(tasks, verbose):
	import csv
	fields = []
	if verbose > 0:
		fields = ['starred', 'type', 'priority']
	fields.append('title')
	fields.append('completed')
	fields.append('due date')
	fields.append('start date')
	if verbose > 0:
		fields.append('alarm')
		fields.append('repeat')
		fields.append('note')
	if verbose > 1:
		fields.append('task uuid')
	writer = csv.writer(sys.stdout, fields, delimiter=';')
	types = {enums.TYPE_PROJECT: 'project',
			enums.TYPE_CHECKLIST: 'checklist',
			enums.TYPE_CHECKLIST_ITEM: 'checklist item',
			enums.TYPE_CALL: 'call',
			enums.TYPE_RETURN_CALL: 'return call',
			enums.TYPE_EMAIL: 'email',
			enums.TYPE_SMS: 'sms'}
	for task in tasks:
		row = [task.title,
				fmt.format_timestamp(task.completed, True),
				fmt.format_timestamp(task.due_date, task.due_time_set),
				fmt.format_timestamp(task.start_date, task.start_time_set)]
		if verbose > 0:
			row.append('*' if task.starred else '')
			row.append(types.get(task.type, 'task'))
			row.append(str(task.priority) if task.priority >= 0 else '')
			row.append(fmt.format_timestamp(task.alarm, True))
			row.append(task.repeat_pattern or '')
			row.append(task.note or '')
		if verbose > 1:
			row.append(task.uuid)
		writer.writerow([col.encode('utf-8') for col in row])
