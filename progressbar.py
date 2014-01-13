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

from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.graphics import style


class ProgressBar(Gtk.Grid):

    def __init__(self, buttons):
        Gtk.Grid.__init__(self)
        self.set_row_spacing(style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)
        self.set_border_width(style.DEFAULT_SPACING * 2)
        self._button_grid = Gtk.Grid()
        self._button_grid.set_row_spacing(style.DEFAULT_SPACING)
        self._button_grid.set_column_spacing(style.DEFAULT_SPACING)
        self._button_grid.set_border_width(style.DEFAULT_SPACING * 2)
        height = 15
        self._button_grid.set_size_request(-1, height)

        logging.error(buttons)
        self._buttons = []
        for i in range(len(buttons)):
            self._buttons.append(Gtk.Button(buttons[i]['label']))
            if 'tooltip' in buttons[i]:
                self._buttons[-1].set_tooltip(buttons[i]['tooltip'])
            logging.error(buttons[i]['label'])
            self._button_grid.attach(self._buttons[-1], i, 0, 1, 1)
            self._buttons[-1].show()
            self._buttons[-1].set_sensitive(False)
        self.attach(self._button_grid, 0, 0, 1, 1)
        self._button_grid.show()

        self._label = Gtk.Label()
        self._label.set_line_wrap(True)
        self._label.set_property('xalign', 0.5)
        self._label.modify_fg(Gtk.StateType.NORMAL,
                              style.COLOR_BUTTON_GREY.get_gdk_color())
        self.attach(self._label, 0, 1, 1, 1)
        self._label.show()

    def set_message(self, message):
        self._label.set_label(message)

    def set_progress(self, i):
        logging.debug('setting button %d to True' % i)
        if i < len(self._buttons):
            self._buttons[i].set_sensitive(True)
