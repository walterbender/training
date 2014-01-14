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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import WebKit

from sugar3.graphics import style
from sugar3.graphics.icon import Icon

import logging
_logger = logging.getLogger('training-activity-page')


class Graphics(Gtk.ScrolledWindow):
    ''' An aligned grid in a scrolling window '''

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        offset = style.GRID_CELL_SIZE
        width = Gdk.Screen.width()
        height = Gdk.Screen.height() - offset * 3
        self.set_size_request(width, height)

        alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        self.add_with_viewport(alignment)
        alignment.show()

        self._grid = Gtk.Grid()
        self._grid.set_row_spacing(style.DEFAULT_SPACING)
        self._grid.set_column_spacing(style.DEFAULT_SPACING)
        self._grid.set_border_width(style.DEFAULT_SPACING * 2)
        alignment.add(self._grid)
        self._grid.show()

        self._row = 0
        self._web_view = None

    def _attach(self, widget):
        self._grid.attach(widget, 0, self._row, 5, 1)
        self._row += 1

    def _attach_two(self, widget1, widget2):
        self._grid.attach(widget1, 0, self._row, 2, 1)
        self._grid.attach(widget2, 3, self._row, 2, 1)
        self._row += 1

    def _attach_center(self, widget):
        self._grid.attach(widget, 2, self._row, 1, 1)
        self._row += 1

    def add_icon(self, icon_name, stroke=style.COLOR_BUTTON_GREY.get_svg(),
                 fill=style.COLOR_TRANSPARENT.get_svg(),
                 icon_size=style.XLARGE_ICON_SIZE):
        icon = Icon(pixel_size=icon_size, icon_name=icon_name,
                    stroke_color=stroke, fill_color=fill)
        self._attach(icon)
        icon.show()

    def add_text(self, text, color=style.COLOR_BLACK.get_html(),
                 size='large', bold=False, justify=Gtk.Justification.LEFT):
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(justify)
        if bold:
            text = '<b>' + text + '</b>'
        span = '<span foreground="%s" size="%s">' % (color, size)
        label.set_markup(span + text + '</span>')
        self._attach(label)
        label.show()

    def add_text_and_icon(self, text, icon_name, size='large', bold=False,
                          color=style.COLOR_BLACK.get_html(),
                          justify=Gtk.Justification.LEFT,
                          stroke=style.COLOR_BUTTON_GREY.get_svg(),
                          fill=style.COLOR_TRANSPARENT.get_svg(),
                          icon_size=style.XLARGE_ICON_SIZE):
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(justify)
        if bold:
            text = '<b>' + text + '</b>'
        span = '<span foreground="%s" size="%s">' % (color, size)
        label.set_markup(span + text + '</span>')

        icon = Icon(pixel_size=icon_size, icon_name=icon_name,
                    stroke_color=stroke, fill_color=fill)

        self._attach_two(label, icon)
        label.show()
        icon.show()

    def add_uri(self, uri):
        self._web_view = WebKit.WebView()
        offset = style.GRID_CELL_SIZE
        width = Gdk.Screen.width() - offset * 2
        height = Gdk.Screen.height() - offset * 5
        self._web_view.set_size_request(width, height)
        self._web_view.set_full_content_zoom(True)
        self._web_view.load_uri(uri)
        self._attach(self._web_view)
        self._web_view.show()

    def set_zoom_level(self, zoom_level):
        if self._web_view is not None:
            self._web_view.set_zoom_level(zoom_level)

    def add_entry(self, text=''):
        entry = Gtk.Entry()
        entry.set_text(text)
        self._attach(entry)
        entry.show()
        return entry

    def add_image(self, image, width=None, height=None):
        if False:  # width is not None and height is not None:
            image = Gtk.Image.new_from_file_at_size(image, width, height)
        else:
            image = Gtk.Image.new_from_file(image)
        self._attach(image)
        image.show()

    def add_button(self, button_label, callback, arg=None):
        button = Gtk.Button()
        button.set_label(button_label)
        self._attach_center(button)
        if arg is None:
            button.connect('clicked', callback)
        else:
            button.connect('clicked', callback, arg)
        button.show()
        return button
