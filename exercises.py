# -*- coding: utf-8 -*-
# Copyright (c) 2013,14 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import os
import json
import time
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GObject

from sugar3.graphics import style

import logging
_logger = logging.getLogger('training-activity-exercises')

from tasks import *
from progressbar import ProgressBar


class Exercises(Gtk.Grid):

    def __init__(self, activity):
        ''' Initialize the task list '''
        Gtk.Grid.__init__(self)
        self.set_row_spacing(style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)

        self._activity = activity
        self._graphics = None
        self._task_button = None
        self.button_was_pressed = True
        self.current_task = None
        self.first_time = True
        self.grid_row_zero = None
        self._current_section = None
        self.counter = 0

        self._task_list = [[IntroTask(self),
                            # HTMLTask(self),
                            EnterNameTask(self),
                            EnterEmailTask(self),
                            ConfirmEmailTask(self),
                            BadgeOneTask(self)],
                           [ProgressSummary(self, 1)],
                           [ChangeNickTask(self),
                            RestoreNickTask(self),
                            BadgeTwoTask(self)],
                           [ProgressSummary(self, 2)],
                           [AddFavoriteTask(self),
                            RemoveFavoriteTask(self),
                            BadgeThreeTask(self)],
                           [ProgressSummary(self, 3)],
                           [FinishedAllTasks(self)]]

        self.current_task = self.read_task_data('current_task')
        if self.current_task is None:
            self.current_task = 0

        self._progress_bar = ProgressBar()
        alignment = Gtk.Alignment.new(xalign=0.5, yalign=0.5,
                                      xscale=0, yscale=0)
        self.attach(alignment, 0, 0, 1, 1)
        alignment.show()
        alignment.add(self._progress_bar)
        self._progress_bar.show()

    def task_button_cb(self, button):
        ''' The button at the bottom of the page for each task: used to
            advance to the next task. '''
        self.button_was_pressed = True
        section, task_index = self.get_section_index()
        self._task_list[section][task_index].after_button_press()
        self.current_task += 1
        self.write_task_data('current_task', self.current_task)
        self.task_master()

    def get_help_info(self):
        ''' Uses help from the Help activity '''
        if self.current_task is None:
            return (None, None)
        else:
            section, index = self.get_section_index()
            return self._task_list[section][index].get_help_info()

    def _run_task(self, section, task_index):
        '''To run a task, we need graphics to display, a test to call that
            returns True or False, and perhaps some data '''

        if self.first_time:
            self._uid = self._task_list[section][task_index].uid
            title, help_file = \
                self._task_list[section][task_index].get_help_info()
            if title is None or help_file is None:
                self._activity.help_button.set_sensitive(False)
            else:
                self._activity.help_button.set_sensitive(True)

            self._load_graphics()

            self._task_data = self.read_task_data(self._uid)
            if self._task_data is None:
                self._task_data = {}
                self._task_data['start_time'] = int(time.time())
                self._task_data['attempt'] = 0
                self._task_data['task'] = \
                    self._task_list[section][task_index].get_name()
                self._task_data['data'] = \
                    self._task_list[section][task_index].get_data()
                self.write_task_data(self._uid, self._task_data)

            self.first_time = False

        GObject.timeout_add(
            self._task_list[section][task_index].get_pause_time(),
            self._test, self._task_list[section][task_index].test,
            self._task_data, self._uid)

    def _test(self, test, task_data, uid):
        ''' Is the task complete? '''
        if test(self, task_data):
            self._task_button.set_sensitive(True)
            task_data = self.read_task_data(uid)
            task_data['end_time'] = int(time.time())
            self.write_task_data(uid, task_data)
        else:
            self._task_data['attempt'] += 1
            self.write_task_data(uid, task_data)
            section, index = self.get_section_index()
            self._run_task(section, index)

    def task_master(self):
        ''' 'nough said. '''
        _logger.debug('Task Master: Running task %d' % (self.current_task))
        self._destroy_graphics()
        self._activity.button_was_pressed = False
        if self.current_task < self.get_number_of_tasks():
            section, task_index = self.get_section_index()
            self.first_time = True
            self._run_task(section, task_index)
        else:
            self._activity.complete = True

    def reload_graphics(self):
        ''' When changing font size and zoom level, we regenerate the task
           graphic. '''
        self._destroy_graphics()
        self._load_graphics()

        section, task_index = self.get_section_index()
        self._test(self._task_list[section][task_index].test,
                   self._task_data, self._uid)

    def _destroy_graphics(self):
        ''' Destroy the graphics from the previous task '''
        if self._graphics is not None:
            self._graphics.destroy()
        if hasattr(self, 'task_button'):
            self._task_button.destroy()

    def _load_graphics(self):
        ''' Load the graphics for a task and define the task button '''
        section, task_index = self.get_section_index()

        self._task_list[section][task_index].set_font_size(
            self._activity.font_size)
        self._task_list[section][task_index].set_zoom_level(
            self._activity.zoom_level)

        self._graphics, self._task_button = \
            self._task_list[section][task_index].get_graphics()
        if self.grid_row_zero is None:
            self.insert_row(0)
            self.grid_row_zero = True
        self.attach(self._graphics, 0, 0, 1, 1)
        self._graphics.show()

        self._task_button.set_sensitive(False)
        self._task_button.show()

        self._update_progress()

    def get_number_of_sections(self):
        return len(self._task_list)

    def get_number_of_tasks_in_section(self, section_index):
        return len(self._task_list[section_index])

    def get_section_index(self):
        count = 0
        for section_index, section in enumerate(self._task_list):
            for task_index in range(len(section)):
                if count == self.current_task:
                    return section_index, task_index
                count += 1
        return -1, -1

    def get_number_of_tasks(self):
        count = 0
        for section in self._task_list:
            count += len(section)
        return count

    def read_task_data(self, uid):
        data_path = os.path.join(self._activity.get_activity_root(), 'data',
                                 'training_data')
        uid_data = None
        if os.path.exists(data_path):
            fd = open(data_path, 'r')
            json_data = fd.read()
            fd.close()
            data = {}
            try:
                if len(json_data) > 0:
                    data = json.loads(json_data)
            except ValueError, e:
                _logger.error('Cannot read training data: %s' % e)
            if uid in data:
                uid_data = data[uid]
        return uid_data

    def write_task_data(self, uid, uid_data):
        data_path = os.path.join(self._activity.get_activity_root(), 'data',
                                 'training_data')
        data = {}
        if os.path.exists(data_path):
            fd = open(data_path, 'r')
            json_data = fd.read()
            fd.close()
            if len(json_data) > 0:
                try:
                    data = json.loads(json_data)
                except ValueError, e:
                    _logger.error('Cannot load training data: %s' % e)
        data[uid] = uid_data
        json_data = json.dumps(data)
        fd = open(data_path, 'w')
        fd.write(json_data)
        fd.close()

    def _update_progress(self):
        section, task_index = self.get_section_index()
        if section < 0:  # We haven't started yet
            return
        tasks_in_section = self.get_number_of_tasks_in_section(section)

        # Adjust numbers:
        #    Count the current task
        #    Don't count badge at end of section task
        task_index += 1
        if tasks_in_section > 1:
            tasks_in_section -= 1

        self._progress_bar.set_progress(task_index / float(tasks_in_section))
        if task_index > tasks_in_section:  # Must be a badge task
            self._progress_bar.set_message(_('Complete'))
        elif task_index == 1 and tasks_in_section == 1:  # Must be a summary
            self._progress_bar.set_message(_('Progress Summary'))
        else:
            self._progress_bar.set_message(
                _('Progress to date: %(current)d / %(total)d' %
                  {'current': task_index, 'total': tasks_in_section}))

        self._activity.progress_label.set_markup(
            '<span foreground="%s" size="%s"><b>%s</b></span>' %
            (style.COLOR_WHITE.get_html(), 'x-large',
             _('Overall: %d%%' % (int((self.current_task * 100.)
                                      / self.get_number_of_tasks())))))
