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

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics import style

from graphics import Graphics, FONT_SIZES

import logging
_logger = logging.getLogger('training-activity-check-progress')


class CheckProgress(Gtk.Grid):

    def __init__(self, task_master):
        Gtk.Grid.__init__(self)
        self.set_row_spacing(0)  # style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)

        self._task_master = task_master

        toolbox = self.build_toolbar()
        graphics = ProgressSummary(self._task_master).get_graphics()

        self.attach(toolbox, 0, 1, 1, 1)
        toolbox.show()
        self.attach(graphics, 0, 2, 1, 1)
        graphics.show()

    def _close_cb(self, button):
        self._task_master.destroy_summary()

    def build_toolbar(self):
        toolbox = ToolbarBox()

        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_markup(
            '<span foreground="%s" size="x-large">%s</span>' %
            (style.COLOR_WHITE.get_html(), _('Progress Summary')))

        item = Gtk.ToolItem()
        item.add(label)
        label.show()

        close = ToolButton('entry-cancel')
        close.connect('clicked', self._close_cb)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)

        toolbox.toolbar.insert(item, -1)
        item.show()
        toolbox.toolbar.insert(separator, -1)
        separator.show()
        toolbox.toolbar.insert(close, -1)
        close.show()

        return toolbox


class ProgressSummary():

    def __init__(self, task_master):
        self._name = _('Progress Summary')
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0
        self._progress = self._task_master.get_completed_sections()

    def _section_button_cb(self, button, section):
        uid = self._task_master.section_and_task_to_uid(section)
        self._task_master.current_task = \
            self._task_master.uid_to_task_number(uid)
        self._task_master.destroy_summary()  # i.e., self.destroy()

    def get_graphics(self):
        colors = []
        strokes = []
        for i in range(self._task_master.get_number_of_sections()):
            if i in self._progress:
                colors.append(style.COLOR_BLACK.get_html())
                strokes.append(style.COLOR_BLACK.get_svg())
            else:
                colors.append(style.COLOR_BUTTON_GREY.get_html())
                strokes.append(style.COLOR_BUTTON_GREY.get_svg())
        graphics = Graphics()
        n = self._task_master.get_number_of_sections()
        for i in range(n):
            if i == 0 or i == n - 1:
                name = self._task_master.get_section_name(i)
            else:
                name = '%d. %s' % (i, self._task_master.get_section_name(i))
            button = graphics.add_text_icon_and_button(
                name,
                self._task_master.get_section_icon(i),
                button_icon='go-right-page',
                size=FONT_SIZES[self._font_size],
                icon_size=style.STANDARD_ICON_SIZE,
                color=colors[i],
                stroke=strokes[i])
            button.connect('clicked', self._section_button_cb, i)
        return graphics
