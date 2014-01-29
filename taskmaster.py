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
from gi.repository import Gdk
from gi.repository import GObject

from sugar3.graphics import style
from sugar3.graphics.toolbutton import ToolButton

import logging
_logger = logging.getLogger('training-activity-taskmaster')

import tasks
from progressbar import ProgressBar
from tests import get_nick, goto_home_view

class TaskMaster(Gtk.Grid):

    def __init__(self, activity):
        ''' Initialize the task list '''
        Gtk.Grid.__init__(self)
        self.set_row_spacing(style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)

        self.button_was_pressed = True
        self.current_task = None
        self.activity = activity
        self.keyname = None

        self._name = None
        self._email = None
        self._graphics = None
        self._summary = None
        self._page = 0
        self._task_button = None
        self._first_time = True
        self._accumulated_time = 0

        self._task_list = tasks.get_tasks(self)
        self._assign_required()

        self.current_task = self.read_task_data('current_task')
        if self.current_task is None:
            self.current_task = 0

        self._graphics_grid = Gtk.Grid()
        self._graphics_grid.set_row_spacing(style.DEFAULT_SPACING)
        self._graphics_grid.set_column_spacing(style.DEFAULT_SPACING)

        graphics_grid_alignment = Gtk.Alignment.new(
            xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        graphics_grid_alignment.add(self._graphics_grid)
        self._graphics_grid.show()
        self.attach(graphics_grid_alignment, 0, 0, 1, 1)
        graphics_grid_alignment.show()

        self._prev_page_button = ToolButton('go-left-page')
        self._prev_page_button.connect('clicked', self._prev_page_cb)
        self._graphics_grid.attach(self._prev_page_button, 0, 7, 1, 1)
        self._next_page_button = ToolButton('go-right-page')
        self._next_page_button.connect('clicked', self._next_page_cb)
        self._graphics_grid.attach(self._next_page_button, 2, 7, 1, 1)

        self._task_button_alignment = Gtk.Alignment.new(
            xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_column_homogeneous(True)

        self._refresh_button = Gtk.Button(_('Refresh Page'))
        self._refresh_button.connect('clicked', self._refresh_button_cb)
        left = Gtk.Alignment.new(xalign=0, yalign=0.5, xscale=0, yscale=0)
        left.add(self._refresh_button)
        self._refresh_button.hide()
        grid.attach(left, 0, 0, 1, 1)
        left.show()

        self._task_button = Gtk.Button(_('Next'))
        self._task_button.connect('clicked', self._task_button_cb)
        mid = Gtk.Alignment.new(xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        mid.add(self._task_button)
        self._task_button.show()
        grid.attach(mid, 1, 0, 1, 1)
        mid.show()

        self._my_turn_button = Gtk.Button(_('My Turn'))
        self._my_turn_button.connect('clicked', self._my_turn_button_cb)
        right = Gtk.Alignment.new(xalign=1.0, yalign=0.5, xscale=0, yscale=0)
        right.add(self._my_turn_button)
        self._my_turn_button.hide()
        grid.attach(right, 2, 0, 1, 1)
        right.show()

        self._task_button_alignment.add(grid)
        grid.show()
        self.attach(self._task_button_alignment, 0, 1, 1, 1)
        self._task_button_alignment.show()

        self._progress_bar = None
        self._progress_bar_alignment = Gtk.Alignment.new(
            xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        self.attach(self._progress_bar_alignment, 0, 2, 1, 1)
        self._progress_bar_alignment.show()

    def keypress_cb(self, widget, event):
        self.keyname = Gdk.keyval_name(event.keyval)

    def task_master(self):
        ''' 'nough said. '''
        if self._summary is not None:
            _logging.debug('Cannot run tasks while summary is displayed')
            return
        _logger.debug('Task Master: Running task %d' % (self.current_task))
        self._destroy_graphics()
        self.activity.button_was_pressed = False
        if self.current_task < self._get_number_of_tasks():
            section, task_index = self.get_section_index()
            # Do we skip this task?
            task = self._task_list[section]['tasks'][task_index]
            if task.is_completed() and task.skip_if_completed():
                _logger.debug('skipping task %d' % task_index)
                self.current_task += 1  # Assume there is a next task
                task_index += 1
            if section > 0:
                self.activity.back.set_sensitive(True)
                if section < len(self._task_list) - 1:
                    self.activity.forward.set_sensitive(True)
            # Check to make sure all the requirements at met
            if not self._check_requirements(section, task_index):
                # Switching to a required task
                section, task_index = self.get_section_index()
            self._first_time = True
            self._run_task(section, task_index)
        else:
            self.activity.complete = True

    def _task_button_cb(self, button):
        ''' The button at the bottom of the page for each task: used to
            advance to the next task. '''
        self.button_was_pressed = True
        section, task_index = self.get_section_index()
        self._task_list[section]['tasks'][task_index].after_button_press()
        self.current_task += 1
        self.write_task_data('current_task', self.current_task)
        self.task_master()

    def _my_turn_button_cb(self, button):
        ''' Take me to the Home Page. '''
        goto_home_view()

    def _refresh_button_cb(self, button):
        ''' Refresh the current page's graphics '''
        section, task_index = self.get_section_index()
        self._graphics.destroy()
        self._graphics, label = \
            self._task_list[section]['tasks'][task_index].get_graphics()

        self._graphics_grid.attach(self._graphics, 1, 0, 1, 15)
        self._graphics.show()

    def get_help_info(self):
        ''' Uses help from the Help activity '''
        if self.current_task is None:
            return (None, None)
        else:
            section, index = self.get_section_index()
            return self._task_list[section]['tasks'][index].get_help_info()

    def _run_task(self, section, task_index):
        '''To run a task, we need graphics to display, a test to call that
            returns True or False, and perhaps some data '''

        task = self._task_list[section]['tasks'][task_index]
        if self._first_time:
            self._uid = task.uid
            title, help_file = task.get_help_info()
            if title is None or help_file is None:
                self.activity.help_button.set_sensitive(False)
            else:
                self.activity.help_button.set_sensitive(True)

            # In order to calculate accumulated time, we need to monitor
            # our start time.
            self._start_time = time.time()
            self._accumulated_time = 0

            self._load_graphics()

            self._task_data = self.read_task_data(self._uid)
            if self._task_data is None:
                self._task_data = {}
                self._task_data['start_time'] = int(self._start_time + 0.5)
                self._task_data['accumulated_time'] = 0
                self._task_data['completed'] = False
                self._task_data['task'] = task.get_name()
                self._task_data['data'] = task.get_data()
                self._task_data['collectable'] = task.is_collectable()
                self.write_task_data(self._uid, self._task_data)
            elif 'completed' in self._task_data and \
                 self._task_data['completed']:
                _logger.debug('Revisiting a completed task')

            self._first_time = False

        GObject.timeout_add(task.get_pause_time(), self._test, task.test,
                            self._task_data, self._uid)

    def _update_accumutaled_time(self, task_data):
        end_time = time.time()
        self._accumulated_time += end_time - self._start_time
        task_data['accumulated_time'] += int(self._accumulated_time + 0.5)
        self._start_time = end_time

    def _test(self, test, task_data, uid):
        ''' Is the task complete? '''
        if test(task_data):
            if self._task_button is not None:
                self._task_button.set_sensitive(True)
            if not 'completed' in task_data or not task_data['completed']:
                task_data = self.read_task_data(uid)
                task_data['end_time'] = int(time.time() + 0.5)
                task_data['completed'] = True
                self._update_accumutaled_time(task_data)
            self.write_task_data(uid, task_data)
        else:
            if self._task_button is not None:
                self._task_button.set_sensitive(False)
            if not 'completed' in task_data or not task_data['completed']:
                self._update_accumutaled_time(task_data)
            self.write_task_data(uid, task_data)
            section, index = self.get_section_index()
            self._run_task(section, index)

    def _assign_required(self):
        ''' Add collectable tasks in each section to badge task. '''
        all_requirements = []
        for section in self._task_list:
            section_requirements = []
            for task in section['tasks']:
                if task.is_collectable():
                    section_requirements.append(task.uid)
                    all_requirements.append(task.uid)
            last = len(section['tasks']) - 1
            if section['tasks'][last].uid[0:5] == 'badge':
                # _logger.debug('setting requirements for %s to %r' %
                #               (section['tasks'][last].uid,
                #                section_requirements))
                section['tasks'][last].set_requires(section_requirements)
        self._task_list[-1]['tasks'][-1].set_requires(all_requirements)
        # _logger.debug('setting requirements for %s to %r' %
        #             (self._task_list[-1]['tasks'][-1].uid, all_requirements))

    def _check_requirements(self, section, task_index, switch_task=True):
        ''' Check to make sure all the requirements at met '''
        requires = self._task_list[section]['tasks'][task_index].get_requires()
        for uid in requires:
            # Don't restrict search to current section
            if not self._uid_to_task(uid, section=None).is_completed():
                if switch_task:
                    _logger.debug(
                        'Task %s required task %s... switching to %s' %
                        (self._task_list[section]['tasks'][task_index].uid,
                         uid, uid))
                    self.current_task = self.uid_to_task_number(uid)
                return False
        return True

    def load_progress_summary(self, summary):
        ''' Interrupt the flow of tasks by showing progress summary '''
        self._destroy_graphics()
        self._progress_bar.hide()
        self._prev_page_button.hide()
        self._next_page_button.hide()
        if hasattr(self, '_summary') and self._summary is not None:
            self._summary.destroy()
        self._summary = summary
        self._graphics_grid.attach(self._summary, 1, 0, 1, 15)
        summary.show()

    def destroy_summary(self):
        ''' Back to tasks '''
        if hasattr(self, '_summary') and self._summary is not None:
            self._summary.destroy()
        self._summary = None
        self.reload_graphics()

    def reload_graphics(self):
        ''' When changing font size and zoom level, we regenerate the task
           graphic. '''
        if self._summary is not None:
            _logging.debug('Cannot run tasks while summary is displayed')
            return
        self._destroy_graphics()
        self._load_graphics()
        self._progress_bar.show()
        section, task_index = self.get_section_index()
        self._test(self._task_list[section]['tasks'][task_index].test,
                   self._task_data, self._uid)

    def _destroy_graphics(self):
        ''' Destroy the graphics from the previous task '''
        if self._graphics is not None:
            self._graphics.destroy()
            # self._graphics = None
        if hasattr(self, '_task_button') and self._task_button is not None:
            self._task_button.hide()

    def _load_graphics(self):
        ''' Load the graphics for a task and define the task button '''
        section, task_index = self.get_section_index()

        self._task_list[section]['tasks'][task_index].set_font_size(
            self.activity.font_size)
        self._task_list[section]['tasks'][task_index].set_zoom_level(
            self.activity.zoom_level)

        self._graphics, label = \
            self._task_list[section]['tasks'][task_index].get_graphics()

        self._graphics_grid.attach(self._graphics, 1, 0, 1, 15)
        self._graphics.show()

        if self._task_list[section]['tasks'][task_index].get_page_count() > 1:
            self._prev_page_button.show()
            self._prev_page_button.set_sensitive(False)
            self._next_page_button.show()
            self._next_page_button.set_sensitive(True)
            self._page = 0
        else:
            self._prev_page_button.hide()
            self._next_page_button.hide()

        if self._task_button is not None:
            self._task_button.set_label(label)
            self._task_button.set_sensitive(False)
            self._task_button.show()

        if self._task_list[section]['tasks'][task_index].get_refresh():
            self._refresh_button.show()
        else:
            self._refresh_button.hide()

        if self._task_list[section]['tasks'][task_index].get_my_turn():
            self._my_turn_button.show()
        else:
            self._my_turn_button.hide()

        self._update_progress()

    def _show_page(self):
        ''' Some tasks have multiple pages '''
        section, task_index = self.get_section_index()
        if self._graphics is not None:
            self._graphics.destroy()
        if hasattr(self, 'task_button'):
            self._task_button.destroy()
        self._graphics, self._task_button = \
            self._task_list[section]['tasks'][task_index].get_graphics(page=self._page)
        self._graphics_grid.attach(self._graphics, 1, 0, 1, 15)
        self._graphics.show()
        if self._task_button is not None:
            self._task_button.set_sensitive(test(self._task_data))
            self._task_button.show()

    def _prev_page_cb(self, button):
        if self._page > 0:
            self._page -= 1
        if self._page == 0:
            self._prev_page_button.set_sensitive(False)
        self._next_page_button.set_sensitive(True)
        self._show_page()

    def _next_page_cb(self, button):
        section, task_index = self.get_section_index()
        count = self._task_list[section]['tasks'][task_index].get_page_count()
        if self._page < count - 1:
            self._page += 1
        if self._page == count - 1:
            self._next_page_button.set_sensitive(False)
        self._prev_page_button.set_sensitive(True)
        self._show_page()

    def get_bundle_path(self):
        return self.activity.bundle_path

    def get_number_of_sections(self):
        return len(self._task_list)

    def get_section_name(self, section):
        return self._task_list[section]['name']

    def get_section_icon(self, section):
        return self._task_list[section]['icon']

    def get_section_index(self):
        count = 0
        for section_index, section in enumerate(self._task_list):
            for task_index in range(len(section['tasks'])):
                if count == self.current_task:
                    return section_index, task_index
                count += 1
        return -1, -1

    def get_completed_sections(self):
        progress = []
        for s, section in enumerate(self._task_list):
            section_completed = True
            for task in section['tasks']:
                if task.is_collectable() and not task.is_completed():
                    section_completed = False
            if section_completed:
                progress.append(s)
        return progress

    def section_and_task_to_uid(self, section, task_index=0):
        if section < 0 or section > self.get_number_of_sections() - 1:
            _logger.error('Bad section number %d' % (section))
            return self._task_list[0]['tasks'][0].uid
        elif task_index < 0 or \
             task_index > len(self._task_list[section]['tasks']) - 1:
            _logger.error('Bad task number %d:%d' % (section, task_index))
            return self._task_list[0]['tasks'][0].uid
        else:
            return self._task_list[section]['tasks'][task_index].uid

    def uid_to_task_number(self, uid):
        i = 0
        for section in self._task_list:
            for task in section['tasks']:
                if task.uid == uid:
                    return i
                i += 1
        _logger.error('UID %s not found' % uid)
        return 0

    def _get_number_of_tasks_in_section(self, section_index):
        return len(self._task_list[section_index]['tasks'])

    def _get_number_of_collectables_in_section(self, section_index):
        count = 0
        for task in self._task_list[section_index]['tasks']:
            if task.is_collectable():
                count += 1
        return count

    def _get_number_of_collectables(self):
        count = 0
        for section_index in range(len(self._task_list)):
            count += self._get_number_of_collectables_in_section(section_index)
        return count

    def _get_number_of_tasks(self):
        count = 0
        for section in self._task_list:
            count += len(section['tasks'])
        return count

    def _uid_to_task(self, uid, section=None):
        if section:
            for task in self._task_list[section]['tasks']:
                if task.uid == uid:
                    return task
        else:
            for section in self._task_list:
                for task in section['tasks']:
                    if task.uid == uid:
                        return task
        _logger.error('UID %s not found' % uid)
        return self._task_list[0]['tasks'][0]

    def _get_number_of_completed_tasks(self):
        count = 0
        for section in self._task_list:
            for task in section['tasks']:
                if task.is_completed():
                    count += 1
        return count

    def _get_number_of_completed_collectables(self):
        count = 0
        for section in self._task_list:
            for task in section['tasks']:
                if task.is_collectable() and task.is_completed():
                    count += 1
        return count

    def read_task_data(self, uid):
        usb_data_path = os.path.join(
            self.activity.volume_data[0]['usb_path'],
            self.activity.volume_data[0]['uid'])
        uid_data = None
        if os.path.exists(usb_data_path):
            fd = open(usb_data_path, 'r')
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
        sugar_data_path = os.path.join(
            self.activity.volume_data[0]['sugar_path'],
            self.activity.volume_data[0]['uid'])
        usb_data_path = os.path.join(
            self.activity.volume_data[0]['usb_path'],
            self.activity.volume_data[0]['uid'])

        # Read before write
        data = {}
        if os.path.exists(usb_data_path):
            fd = open(usb_data_path, 'r')
            json_data = fd.read()
            fd.close()
            if len(json_data) > 0:
                try:
                    data = json.loads(json_data)
                except ValueError, e:
                    _logger.error('Cannot load training data: %s' % e)
        data[uid] = uid_data

        # Make sure the volume UID is present
        data['training_data_uid'] = self.activity.volume_data[0]['uid']

        # Write to the USB and ...
        json_data = json.dumps(data)
        fd = open(usb_data_path, 'w')
        fd.write(json_data)
        fd.close()
        # ... save shadow copy in Sugar
        fd = open(sugar_data_path, 'w')
        fd.write(json_data)
        fd.close()

    def _prev_task_button_cb(self, button):
        section, task_index = self.get_section_index()
        if task_index == 0:
            return
        task = task_index
        while(task > 0):
            task -= 1
            if self._check_requirements(section, task, switch_task=False):
                self.current_task -= (task_index - task)
                break
        section, task_index = self.get_section_index()
        _logger.debug('running task %d:%d from prev task button' %
                      (section, task_index))
        self.task_master()

    def _next_task_button_cb(self, button):
        section, task_index = self.get_section_index()
        tasks_in_section = self._get_number_of_tasks_in_section(section)
        if task_index > tasks_in_section - 1:
            return
        task = task_index + 1
        while(task < tasks_in_section - 1):
            if self._check_requirements(section, task, switch_task=False):
                self.current_task += (task - task_index)
                break
            task += 1
        section, task_index = self.get_section_index()
        _logger.debug('running task %d:%d from next task button' %
                      (section, task_index))
        self.task_master()

    def _look_for_next_task(self):
        section, task_index = self.get_section_index()
        tasks_in_section = self._get_number_of_tasks_in_section(section)
        if task_index > tasks_in_section - 1:
            return False
        task = task_index + 1
        while(task < tasks_in_section - 1):
            if self._check_requirements(section, task, switch_task=False):
                return True
            task += 1
        return False

    def _progress_button_cb(self, button, i):
        section, task_index = self.get_section_index()
        _logger.debug('running task %d:%d from progess button' % (section, i))
        self.current_task += (i - task_index)
        self.task_master()

    def _update_progress(self):
        section, task_index = self.get_section_index()
        if section < 0:  # We haven't started yet
            return
        tasks_in_section = self._get_number_of_tasks_in_section(section)

        # If the task index is 0, then we need to create a new progress bar
        if task_index == 0 or self._progress_bar is None:
            if self._progress_bar is not None:
                self._progress_bar.destroy()

            buttons = []
            if tasks_in_section > 1:
                for i in range(tasks_in_section - 1):
                    buttons.append(
                        {'label': str(i + 1),
                         'tooltip':
                         self._task_list[section]['tasks'][i].get_name()})

            if self._name is None:
                self._name = self.read_task_data('name')
            if self._email is None:
                self._email = self.read_task_data('email_address')
            if self._name is not None and self._email is not None:
                name = '%s\n%s' % (self._name, self._email)
            elif self._name is not None:
                name = self._name
            else:
                name = ''

            self._progress_bar = ProgressBar(name,
                                             self._task_list[section]['name'],
                                             buttons,
                                             self._prev_task_button_cb,
                                             self._next_task_button_cb,
                                             self._progress_button_cb)
            self._progress_bar_alignment.add(self._progress_bar)
            self._progress_bar.show()

        if tasks_in_section == 1:
            self._progress_bar.hide_prev_next_task_buttons()
        else:
            self._progress_bar.show_prev_next_task_buttons()

        # Set button sensitivity True for completed tasks and current task
        _logger.debug('task_index: %d; tasks_in_section: %d' %
                      (task_index, tasks_in_section))
        if task_index < tasks_in_section:
            for task in range(tasks_in_section - 1):
                if self._task_list[section]['tasks'][task].is_completed():
                    self._progress_bar.set_button_sensitive(task, True)
                else:
                    self._progress_bar.set_button_sensitive(task, False)
            # Current task (last task in section has no button)
            if task_index < tasks_in_section - 1:
                self._progress_bar.set_button_sensitive(task_index, True)

        if task_index > 0:
            self._progress_bar.prev_task_button.set_sensitive(True)
        else:
            self._progress_bar.prev_task_button.set_sensitive(False)

        if self._look_for_next_task():
            self._progress_bar.next_task_button.set_sensitive(True)
        else:
            self._progress_bar.next_task_button.set_sensitive(False)

        self.activity.progress_label.set_markup(
            '<span foreground="%s" size="%s"><b>%s</b></span>' %
            (style.COLOR_WHITE.get_html(), 'x-large',
             _('Overall: %d%%' % (int(
                 (self._get_number_of_completed_collectables() * 100.)
                 / self._get_number_of_collectables())))))
