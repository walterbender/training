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

from sugar3.graphics import style


class HelpPanel(Gtk.Grid):

    def __init__(self, task_master):
        Gtk.Grid.__init__(self)
        self.set_row_spacing(style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)
        self.set_column_homogeneous(True)
        # self.set_row_homogeneous(True)
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
        info_label = Gtk.Label()
        info_label.set_use_markup(True)
        info_label.set_justify(Gtk.Justification.LEFT)
        info_label.set_markup(
            '<span foreground="%s" size="large">%s</span>' %
            (style.COLOR_WHITE.get_html(), _('Or use the form below:')))
        alignment.add(info_label)
        info_label.show()
        self.attach(alignment, 0, 4, 4, 1)
        alignment.show()

        feedback_button = Gtk.RadioButton(label=_('Feedback'))
        self.attach(feedback_button, 0, 5, 1, 1)
        feedback_button.connect('clicked', self._feedback_button_cb)
        feedback_button.show()

        help_button = Gtk.RadioButton(label=_('Help'), group=feedback_button)
        self.attach(help_button, 1, 5, 1, 1)
        help_button.connect('clicked', self._help_button_cb)
        help_button.show()

        self._entry = Gtk.TextView()
        self._entry.set_wrap_mode(Gtk.WrapMode.WORD)
        self._entry.set_size_request(-1, style.GRID_CELL_SIZE * 2)
        self._text_buffer = self._entry.get_buffer()
        self._text_buffer.set_text(_('Type question here...'))
        self.attach(self._entry, 0, 6, 4, 4)
        self._entry.show()

        self._check_button = Gtk.CheckButton(label=_('Include screenshot?'))
        self._check_button.set_mode(True)
        self.attach(self._check_button, 0, 10, 2, 1)
        self._check_button.show()

        send_button = Gtk.Button(_('Send'))
        self.attach(send_button, 3, 10, 1, 1)
        send_button.connect('clicked', self._send_button_cb)
        send_button.show()

    def _feedback_button_cb(self, widget=None):
        self._mode = 'feedback'

    def _help_button_cb(self, widget=None):
        self._mode = 'help'

    def _send_button_cb(self, widget=None):
        bounds = self._text_buffer.get_bounds()
        text = self._text_buffer.get_text(bounds[0], bounds[1], True)
        screen_shot = self._check_button.get_mode()
        section_index, task_index = \
            self._task_master._get_section_and_task_index()

        logging.debug('SEND: %s: (%d:%d) %s (screenshot %s)' %
                      (self._mode, section_index, task_index,
                      text, str(screen_shot)))
        # DO SOMETHING HERE
