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

from graphics import Graphics
from tasks import FONT_SIZES

import logging
_logger = logging.getLogger('training-activity-check-progress')


class CheckProgress(Gtk.Window):
    def __init__(self, exercises):
        Gtk.Window.__init__(self)

        self.set_destroy_with_parent(True)
        self.set_size_request(int(Gdk.Screen.width() / 1.5),
                              int(Gdk.Screen.height() / 1.5))
        self.set_decorated(False)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        self.set_modal(True)
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('white'))

        grid = Gtk.Grid()
        toolbox = self.build_toolbar()
        graphics = ProgressSummary(exercises).get_graphics()

        grid.attach(toolbox, 0, 1, 1, 1)
        toolbox.show()
        grid.attach(graphics, 0, 2, 1, 1)
        graphics.show()

        self.add(grid)
        grid.show()

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
        close.connect('clicked', lambda x: self.destroy())

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
    _SECTIONS = [{'name': _('Welcome to One Academy'),
                  'icon': 'badge-intro'},
                 {'name': _('Getting to Know the XO'),
                  'icon': 'badge-intro'},
                 {'name': _('More sections listed here'),
                  'icon': 'badge-intro'}]

    def __init__(self, activity):
        self._name = _('Progress Summary')
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0
        self._progress = self._activity.get_completed_sections()

    def get_graphics(self):
        colors = []
        strokes = []
        for i in range(len(self._SECTIONS)):
            if i in self._progress:
                colors.append(style.COLOR_BLACK.get_html())
                strokes.append(style.COLOR_BLACK.get_svg())
            else:
                colors.append(style.COLOR_BUTTON_GREY.get_html())
                strokes.append(style.COLOR_BUTTON_GREY.get_svg())
        graphics = Graphics(
            width=int(Gdk.Screen.width() / 1.5),
            height=int(Gdk.Screen.height() / 1.5 - style.GRID_CELL_SIZE))
        for i in range(len(self._SECTIONS)):
            graphics.add_text_and_icon(self._SECTIONS[i]['name'],
                                       self._SECTIONS[i]['icon'],
                                       size=FONT_SIZES[self._font_size],
                                       icon_size=style.LARGE_ICON_SIZE,
                                       color=colors[i],
                                       stroke=strokes[i])
        return graphics
