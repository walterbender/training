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

import logging
_logger = logging.getLogger('training-activity-progressbar')

from gi.repository import Gtk

from sugar3.graphics import style

_HEIGHT = 15
_BLACK = style.COLOR_BLACK.get_html()
_WHITE = style.COLOR_WHITE.get_html()
_SIZE = 'small'


class ProgressBar(Gtk.Grid):

    def __init__(self, user_name, section_name, uid, progress_button_data,
                 prev_task_button_cb, next_task_button_cb, progress_button_cb):
        Gtk.Grid.__init__(self)

        self.set_row_spacing(style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)
        self.set_border_width(0)  # style.DEFAULT_SPACING * 2)
        self.set_column_homogeneous(True)

        alignment1 = Gtk.Alignment.new(
            xalign=1.0, yalign=0.5, xscale=0, yscale=0)
        self._section_label = Gtk.Label()
        self._section_label.set_use_markup(True)
        self._section_label.set_justify(Gtk.Justification.LEFT)
        span = '<span foreground="%s" size="%s">' % (_BLACK, _SIZE)
        self._section_label.set_markup('%s%s\n%s</span>' %
                                       (span, section_name, uid))
        alignment1.add(self._section_label)
        self._section_label.show()

        alignment2 = Gtk.Alignment.new(
            xalign=1.0, yalign=0.5, xscale=0, yscale=0)
        self.prev_task_button = Gtk.Button('<')
        self.prev_task_button.connect('clicked', prev_task_button_cb)
        grid = Gtk.Grid()
        grid.set_row_spacing(0)  # style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(0)  # style.DEFAULT_SPACING * 2)
        grid.set_size_request(-1, _HEIGHT)
        grid.attach(self.prev_task_button, 0, 0, 1, 1)
        self.prev_task_button.show()
        self.prev_task_button.set_sensitive(False)
        alignment2.add(grid)
        grid.show()

        alignment3 = Gtk.Alignment.new(
            xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        grid = Gtk.Grid()
        grid.set_row_spacing(0)  # style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(0)  # style.DEFAULT_SPACING * 2)
        grid.set_size_request(-1, _HEIGHT)
        self._progress_buttons = []
        for i, button_data in enumerate(progress_button_data):
            self._progress_buttons.append(Gtk.Button(button_data['label']))
            if 'tooltip' in button_data:
                tooltip = \
'<span background="%s" foreground="%s" size="%s"> %s </span>' \
                    % (_WHITE, _BLACK, _SIZE, button_data['tooltip'])
                self._progress_buttons[i].connect(
                    'clicked', progress_button_cb, i)
                self._progress_buttons[i].set_tooltip_markup(tooltip)
            grid.attach(
                self._progress_buttons[i], i, 0, 1, 1)
            self._progress_buttons[i].show()
            self._progress_buttons[-1].set_sensitive(False)
        alignment3.add(grid)
        grid.show()

        alignment4 = Gtk.Alignment.new(
            xalign=0, yalign=0.5, xscale=0, yscale=0)
        self.next_task_button = Gtk.Button('>')
        self.next_task_button.connect('clicked', next_task_button_cb)
        grid = Gtk.Grid()
        grid.set_row_spacing(0)  # style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(0)  # style.DEFAULT_SPACING * 2)
        grid.set_size_request(-1, _HEIGHT)
        grid.attach(self.next_task_button, 0, 0, 1, 1)
        self.next_task_button.show()
        self.next_task_button.set_sensitive(False)
        alignment4.add(grid)
        grid.show()

        alignment5 = Gtk.Alignment.new(
            xalign=0, yalign=0.5, xscale=0, yscale=0)
        self._name_label = Gtk.Label()
        self._name_label.set_use_markup(True)
        self._name_label.set_justify(Gtk.Justification.RIGHT)
        span = '<span foreground="%s" size="%s">' % (_BLACK, _SIZE)
        self._name_label.set_markup(span + user_name + '</span>')
        alignment5.add(self._name_label)
        self._name_label.show()

        n = len(progress_button_data)
        c = 0
        self.attach(alignment1, c, 1, 6, 1)
        alignment1.show()
        c += 6
        self.attach(alignment2, c, 1, 2, 1)
        alignment2.show()
        c += 2
        self.attach(alignment3, c, 1, n, 1)
        alignment3.show()
        c += n
        self.attach(alignment4, c, 1, 2, 1)
        alignment4.show()
        c += 2
        self.attach(alignment5, c, 1, 6, 1)
        alignment5.show()
        c += 6

        box = Gtk.EventBox()
        box.modify_bg(Gtk.StateFlags.NORMAL,
                      style.COLOR_BLACK.get_gdk_color())
        box.set_size_request(-1, 2)
        self.attach(box, 0, 0, c, 1)
        box.show()

    def set_button_sensitive(self, i, flag=True):
        for b, button in enumerate(self._progress_buttons):
            if b == i:
                button.set_sensitive(flag)
                button.set_label('★')
            else:
                button.set_label('%x' % (b + 1))

    def hide_prev_next_task_buttons(self):
        self.prev_task_button.hide()
        self.next_task_button.hide()

    def show_prev_next_task_buttons(self):
        self.prev_task_button.show()
        self.next_task_button.show()
