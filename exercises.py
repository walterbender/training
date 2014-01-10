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
from gi.repository import WebKit

from sugar3.graphics import style
from sugar3.graphics.icon import Icon

import logging
_logger = logging.getLogger('training-activity-exercises')

from tasks import *


FONT_SIZES = ['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large',
              'xx-large']


class Exercises():

    def __init__(self, activity):
        self._activity = activity
        self.button_was_pressed = True
        self.current_task = None
        self.first_time = True
        self.grid_row_zero = None
        self._current_section = None
        self.counter = 0

        self._task_list = [[IntroTask(self),
                            EnterNameTask(self),
                            EnterEmailTask(self)],
                           [ChangeNickTask(self),
                            RestoreNickTask(self)],
                           [AddFavoriteTask(self),
                            RemoveFavoriteTask(self)],
                           [FinishedAllTasks(self)]]

        self.current_task = self.read_task_data('current_task')
        if self.current_task is None:
            self.current_task = 0
        _logger.error('LEAVING INIT %d' % self.current_task)

    def create_task_button(self, label=_('Next')):
        _logger.error('CREATING TASK BUTTON %s' % label)

        def __button_cb(button, self):
            _logger.error('BUTTON PRESS')
            self.button_was_pressed = True
            section, task_index = self.get_section_index()
            self._task_list[section][task_index].after_button_press()
            self.current_task += 1
            _logger.error('INCREMENTING TASK COUNTER')
            self.write_task_data('current_task', self.current_task)
            _logger.error('WRITING CURRENT TASK %d' % (self.current_task))
            self._activity.update_progress()
            self.task_master()

        self.task_button = Gtk.Button(label)
        self.task_button.connect('clicked', __button_cb, self)

    def get_help_info(self):
        _logger.error('get_help_info for task %d' % self.current_task)
        if self.current_task is None:
            return (None, None)
        else:
            section, index = self.get_section_index()
            return self._task_list[section][index].get_help_info()

    def _run_task(self, section, task_index):
        ''' To run a task, we need a message to display,
            a task method to call that returns True or False,
            and perhaps some data '''
        _logger.error('RUN TASK %d %d' % (section, task_index))

        prompt = self._task_list[section][task_index].get_prompt()
        data = self._task_list[section][task_index].get_data()
        test = self._task_list[section][task_index].test
        uid = self._task_list[section][task_index].uid
        success = self._task_list[section][task_index].get_success()
        retry = self._task_list[section][task_index].get_retry()
        title, help_file = \
            self._task_list[section][task_index].get_help_info()
        pause = self._task_list[section][task_index].get_pause_time()

        if title is None or help_file is None:
            self._activity.help_button.set_sensitive(False)
        else:
            self._activity.help_button.set_sensitive(True)

        _logger.error('FIRST TIME: %s' % (str(self.first_time)))
        # Set up the task the first time through
        if self.first_time:
            _logger.error('CREATING SCROLLED WINDOW')
            self.scroll_window = Gtk.ScrolledWindow()
            self.scroll_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            self.scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                          Gtk.PolicyType.AUTOMATIC)
            offset = style.GRID_CELL_SIZE
            width = Gdk.Screen.width()
            height = Gdk.Screen.height() - offset * 3
            self.scroll_window.set_size_request(width, height)
            graphics = self._task_list[section][task_index].get_graphics()
            self.scroll_window.add(graphics)
            graphics.show()
            self.scroll_window.show()
            if self.grid_row_zero is None:
                _logger.error('ADDING ROW 0')
                self._activity.grid.insert_row(0)
                self.grid_row_zero = True
            _logger.error('ATTACHING SCROLL WINDOW TO GRID')
            self._activity.grid.attach(self.scroll_window, 0, 0, 1, 1)
            self._activity.grid.show()

            _logger.error('SETTING BUTTON INSENSITIVE')
            self.task_button.set_sensitive(False)
            self.task_button.show()
            _logger.error('UPDATE PROGRESS')
            self._activity.update_progress()

        task_data = self.read_task_data(uid)
        if task_data is None:
            task_data = {}
            task_data['start_time'] = int(time.time())
            task_data['task'] = prompt
            task_data['attempt'] = 0
            task_data['data'] = data
            self.write_task_data(uid, task_data)

        if self.first_time:
            _logger.error('SETTING FIRSTTIME FALSE')
            self.first_time = False

        _logger.error('CALL TEST IN %d MSEC' % pause)
        GObject.timeout_add(pause, self._test, test, task_data,
                            uid, retry, success)

    def _test(self, test, task_data, uid, retry, success):
        _logger.error('IN TEST')
        if test(self, task_data):
            _logger.error('PASSED')
            self.task_button.set_sensitive(True)
            _logger.error('BUTTON ENABLED')
            # Record end time
            task_data = self.read_task_data(uid)
            task_data['end_time'] = int(time.time())
            self.write_task_data(uid, task_data)
            _logger.error('WRITING TASK DATA')
        else:
            _logger.error('FAILED')
            if 'attempt' in task_data:
                task_data['attempt'] += 1
            self.write_task_data(uid, task_data)
            _logger.error('WRITING TASK DATA')
            section, index = self.get_section_index()
            _logger.error('%d %d %d' % (self.current_task, section, index))
            self._run_task(section, index)

    def task_master(self):
        _logger.error('TASK MASTER: RUNNING TASK %d' % (self.current_task))
        if hasattr(self, 'scroll_window'):
            _logger.error('DESTROYING SCROLL WINDOW')
            self.scroll_window.destroy()
        if hasattr(self, 'task_button'):
            _logger.error('DESTROYING TASK BUTTON')
            self.task_button.destroy()
        self._activity.button_was_pressed = False
        # Do we have more tasks to run?
        if self.current_task < self.get_number_of_tasks():
            section, index = self.get_section_index()
            self.first_time = True
            self._run_task(section, index)
            _logger.error('BACK FROM RUN TASK')
        else:
            self._activity.complete = True
            self.task_button_label.set_text(_('Finished!'))

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
                data = json.loads(json_data)
        data[uid] = uid_data
        json_data = json.dumps(data)
        fd = open(data_path, 'w')
        fd.write(json_data)
        fd.close()

    def make_intro_graphic(self, prompt, image, button_label=_('Next')):
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        center_in_panel.add(grid)
        grid.show()

        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_markup(prompt)
        grid.attach(label, 0, 0, 1, 1)
        label.show()

        icon = Icon(pixel_size=style.XLARGE_ICON_SIZE,
                    icon_name=image,
                    stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                    fill_color=style.COLOR_TRANSPARENT.get_svg())
        grid.attach(icon, 0, 1, 1, 1)
        icon.show()

        self.create_task_button()
        grid.attach(self.task_button, 0, 2, 1, 1)
        self.task_button.set_label(button_label)
        self.task_button.show()
        return center_in_panel

    def make_html_graphic(self, uri, button_label=_('Next')):
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        center_in_panel.add(grid)
        grid.show()

        web_view = WebKit.WebView()
        offset = style.GRID_CELL_SIZE
        width = Gdk.Screen.width() - offset * 2
        height = Gdk.Screen.height() - offset * 2
        web_view.set_size_request(width, height)
        web_view.set_full_content_zoom(True)
        web_view.load_uri(uri)
        grid.attach(web_view, 0, 0, 1, 1)
        web_view.show()

        self.create_task_button()
        grid.attach(self.task_button, 0, 1, 1, 1)
        self.task_button.set_label(button_label)
        self.task_button.show()
        return center_in_panel

    def make_entry_graphic(self, task, dictionary, button_label=_('Next')):
        ''' dictionary is [{'title':, 'text':, 'caption': }, ]'''

        _logger.error('MAKE ENTRY GRAPHIC')
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        center_in_panel.add(grid)
        grid.show()
        g = 0
        for i in range(len(dictionary)):
            text = dictionary[i].get('text', '')
            title = dictionary[i].get('title', None)
            maxwidth = dictionary[i].get('max', 60)
            tooltip = dictionary[i].get('tooltip', None)
            caption = dictionary[i].get('caption', None)
            if title is not None:
                title_label = Gtk.Label(
                    '<span foreground="%s" size="x-large"><b>%s</b></span>' %
                    (style.COLOR_BLACK.get_html(), title))
                title_label.set_use_markup(True)
                title_label.set_line_wrap(True)
                title_label.set_property('xalign', 0.5)
                grid.attach(title_label, 0, g, 1, 1)
                g += 1
                title_label.show()
            if caption is not None:
                caption_label = Gtk.Label(
                    '<span background="%s" foreground="%s" size="x-large">\
%s</span>' %
                    (style.COLOR_WHITE.get_html(),
                     style.COLOR_BUTTON_GREY.get_html(), caption))
                caption_label.set_use_markup(True)
                caption_label.set_line_wrap(True)
                caption_label.set_property('xalign', 0.5)
                grid.attach(caption_label, 0, g, 1, 1)
                g += 1
                caption_label.show()

            entry = Gtk.Entry()
            task.entries.append(entry)
            _logger.error('APPENDING NEW ENTRY')
            _logger.error(task.entries)
            entry.set_text(text)
            if tooltip is not None and hasattr(entry, 'set_tooltip_text'):
                entry.set_tooltip_text(tooltip)
                entry.set_width_chars(maxwidth)
            grid.attach(entry, 0, g, 1, 1)
            entry.show()
            g += 1

        self.create_task_button()
        grid.attach(self.task_button, 0, g, 1, 1)
        self.task_button.set_label(button_label)
        self.task_button.show()
        return center_in_panel

    def make_image_graphic(self, dictionary, button_label=_('Next')):
        ''' dictionary is [{'title':, 'path':, 'caption': }, ]'''
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        row = 0
        for i in range(len(dictionary)):
            title = dictionary[i].get('title', None)
            path = dictionary[i].get('path', None)
            caption = dictionary[i].get('caption', None)
            if title is not None:
                title_label = Gtk.Label(
                    '<span foreground="%s" size="x-large"><b>%s</b></span>' %
                    (style.COLOR_BLACK.get_html(), title))
                title_label.set_use_markup(True)
                title_label.set_line_wrap(True)
                title_label.set_property('xalign', 0.5)
                grid.attach(title_label, 0, row, 1, 1)
                row += 1
                title_label.show()
            if path is not None:
                alignment_box = Gtk.Alignment.new(xalign=0.5, yalign=0.5,
                                                  xscale=0, yscale=0)
                grid.attach(alignment_box, 0, row, 1, 1)
                row += 1
                image = Gtk.Image.new_from_file(path)
                alignment_box.add(image)
                image.show()
                alignment_box.show()
            if caption is not None:
                caption_label = Gtk.Label(
                    '<span background="%s" foreground="%s" size="x-large">\
%s</span>' %
                    (style.COLOR_WHITE.get_html(),
                     style.COLOR_BUTTON_GREY.get_html(), caption))
                caption_label.set_use_markup(True)
                caption_label.set_line_wrap(True)
                caption_label.set_property('xalign', 0.5)
                grid.attach(caption_label, 0, row, 1, 1)
                row += 1
                caption_label.show()
        self.create_task_button()
        grid.attach(self.task_button, 0, row, 1, 1)
        self.task_button.set_label(button_label)
        self.task_button.show()
        return grid
