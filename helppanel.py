#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Walter Bender
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import logging
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GObject

from sugar3.graphics import style
from sugar3.graphics.radiotoolbutton import RadioToolButton

from activity import NAME_UID, EMAIL_UID, SCHOOL_UID
import utils


class HelpPanel(Gtk.Grid):

    def __init__(self, task_master):
        Gtk.Grid.__init__(self)
        self.set_row_spacing(style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)
        self.set_column_homogeneous(True)
        self.set_border_width(style.DEFAULT_SPACING)

        self._task_master = task_master
        self._mode = 'feedback'

        alignment = Gtk.Alignment.new(0., 0.5, 0., 0.)
        phone_label = Gtk.Label()
        phone_label.set_use_markup(True)
        phone_label.set_justify(Gtk.Justification.LEFT)
        phone_label.set_markup(
            '<span foreground="%s" size="large">%s</span>' %
            (style.COLOR_WHITE.get_html(), _('Call: 1-800 ONE EDU\n'
                                             'Email: info@one-education.org')))
        alignment.add(phone_label)
        phone_label.show()
        self.attach(alignment, 0, 0, 4, 1)
        alignment.show()

        alignment = Gtk.Alignment.new(0., 0.5, 0., 0.)
        self._info_label = Gtk.Label()
        self._info_label.set_use_markup(True)
        self._info_label.set_justify(Gtk.Justification.LEFT)
        self._info_label.set_markup(
            '<span foreground="%s" size="large">%s</span>' %
            (style.COLOR_WHITE.get_html(), _('Or use the form below:')))
        alignment.add(self._info_label)
        self._info_label.show()
        self.attach(alignment, 0, 4, 4, 1)
        alignment.show()

        grid = Gtk.Grid()
        self._feedback_button = RadioToolButton(group=None)
        self._feedback_button.set_icon_name('edit-description')
        self._feedback_button.connect('clicked', self._feedback_button_cb)
        grid.attach(self._feedback_button, 0, 0, 1, 1)
        self._feedback_button.show()

        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_markup('<span foreground="%s" size="large">%s</span>' %
                         (style.COLOR_WHITE.get_html(), _('Send feedback')))
        grid.attach(label, 1, 0, 1, 1)
        label.show()

        alignment = Gtk.Alignment.new(0., 0.5, 0., 0.)
        alignment.add(grid)
        grid.show()
        self.attach(alignment, 0, 5, 2, 1)
        alignment.show()

        grid = Gtk.Grid()
        self._help_button = RadioToolButton(group=self._feedback_button)
        self._help_button.set_icon_name('toolbar-help-gray')
        self._help_button.connect('clicked', self._help_button_cb)
        grid.attach(self._help_button, 0, 0, 1, 1)
        self._help_button.show()

        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_markup('<span foreground="%s" size="large">%s</span>' %
                         (style.COLOR_WHITE.get_html(), _('Ask for help')))
        grid.attach(label, 1, 0, 1, 1)
        label.show()

        alignment = Gtk.Alignment.new(0., 0.5, 0., 0.)
        alignment.add(grid)
        grid.show()
        self.attach(alignment, 2, 5, 2, 1)
        alignment.show()

        self._feedback_button.set_active(True)

        self._entry = Gtk.TextView()
        self._entry.set_wrap_mode(Gtk.WrapMode.WORD)
        self._entry.set_size_request(-1, style.GRID_CELL_SIZE * 2)
        self._text_buffer = self._entry.get_buffer()
        self._text_buffer.set_text(_('Type question here...'))
        self.attach(self._entry, 0, 6, 4, 4)
        self._entry.show()

        self._check_button = Gtk.CheckButton(label=_('Include screenshot?'))
        self._check_button.set_active(True)
        self.attach(self._check_button, 0, 10, 2, 1)
        self._check_button.show()

        self._send_button = Gtk.Button(_('Send'))
        self.attach(self._send_button, 3, 10, 1, 1)
        self._send_button.connect('clicked', self._send_button_cb)
        self._send_button.show()

    def set_connected(self, connected):
        if connected:
            self._info_label.set_markup(
                '<span foreground="%s" size="large">%s</span>' %
                (style.COLOR_WHITE.get_html(), _('Or use the form below:')))
            self._send_button.set_sensitive(True)
        else:
            self._info_label.set_markup(
                '<span foreground="%s" size="large">%s</span>' %
                (style.COLOR_WHITE.get_html(),
                 _('You must be connected to the Internet to use '
                   'the form below.')))
            self._send_button.set_sensitive(True)  # False)

    def _feedback_button_cb(self, widget=None):
        self._mode = 'feedback'
        self._feedback_button.set_icon_name('edit-description')
        self._help_button.set_icon_name('toolbar-help-gray')

    def _help_button_cb(self, widget=None):
        self._mode = 'help'
        self._feedback_button.set_icon_name('edit-description-gray')
        self._help_button.set_icon_name('toolbar-help')

    def _send_button_cb(self, widget=None):
        self._task_master.activity.help_palette.popdown(immediate=True)
        # idle_add was not sufficient... adding a delay
        GObject.timeout_add(2000, self._take_screen_shot_and_send)

    def _take_screen_shot_and_send(self):
        # These should always exist.
        bounds = self._text_buffer.get_bounds()
        text = self._text_buffer.get_text(bounds[0], bounds[1], True)
        log_file_path = utils.get_log_file('org.sugarlabs.Training')
        section_index, task_index = \
            self._task_master.get_section_and_task_index()

        data = {'ticket': self._mode, 'section': section_index,
                'task': task_index, 'entry': text, 'log': log_file_path}

        # But any of these could be None.
        email = self._task_master.read_task_data(EMAIL_UID)
        if email is not None:
            data['email'] = email

        name = self._task_master.read_task_data(NAME_UID)
        if name is not None:
            data['name'] = name

        school = self._task_master.read_task_data(SCHOOL_UID)
        if school is not None:
            data['school'] = school

        logging.debug(self._check_button.get_mode())
        if self._check_button.get_active():
            data['screenshot'] = utils.take_screen_shot()

        # HAND THE DATA OFF HERE TO ZENDESK
        logging.debug(data)
