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

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import WebKit

from sugar3.graphics import style
from sugar3.graphics.icon import Icon
from sugar3.graphics.toolbutton import ToolButton

import logging
_logger = logging.getLogger('training-activity-graphics')

# Repeated font sizes at the end to enable web graphics to continue to scale
FONT_SIZES = ['xx-small', 'x-small', 'small', 'medium', 'large', 'large',
              'x-large', 'x-large', 'x-large', 'xx-large', 'xx-large',
              'xx-large']


class Graphics(Gtk.Alignment):
    ''' An aligned grid in a scrolling window '''

    def __init__(self, width=None, height=None):
        Gtk.Alignment.__init__(self)

        if width is None:
            width = Gdk.Screen.width() - style.GRID_CELL_SIZE
        if height is None:
            height = Gdk.Screen.height() - style.GRID_CELL_SIZE * 3
        self.set_size_request(width, height)

        self.set(0.5, 0, 0, 0)

        self._grid = Gtk.Grid()
        self._grid.set_row_spacing(style.DEFAULT_SPACING)
        self._grid.set_column_spacing(style.DEFAULT_SPACING)
        self._grid.set_border_width(style.DEFAULT_SPACING * 2)
        self.add(self._grid)
        self._grid.show()

        self._row = 0
        self._web_view = None

    def _attach(self, widget):
        self._grid.attach(widget, 0, self._row, 5, 1)
        self._row += 1

    def _attach_two(self, widget1, widget2):
        alignment = Gtk.Alignment.new(0, 0.5, 0, 0)
        alignment.add(widget1)
        self._grid.attach(alignment, 0, self._row, 2, 1)
        alignment.show()
        self._grid.attach(widget2, 3, self._row, 2, 1)
        self._row += 1

    def _attach_three(self, widget1, widget2, widget3):
        alignment = Gtk.Alignment.new(0, 0.5, 0, 0)
        alignment.add(widget1)
        self._grid.attach(alignment, 0, self._row, 3, 1)
        alignment.show()
        self._grid.attach(widget2, 3, self._row, 1, 1)
        self._grid.attach(widget3, 4, self._row, 1, 1)
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

    def add_text_icon_and_button(self, text, icon_name,
                                 button_icon=None,
                                 button_label=None,
                                 size='large', bold=False,
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

        if button_icon is not None:
            button = ToolButton(button_icon)
        else:
            button = Gtk.Button()
            button.set_label(button_label)
        self._attach_three(label, icon, button)
        label.show()
        icon.show()
        button.show()
        return button

    def add_uri(self, uri, height=610):
        self._web_view = WebKit.WebView()
        width = Gdk.Screen.width() - style.GRID_CELL_SIZE
        height = int(height * Gdk.Screen.height() / 900.)
        self._web_view.set_size_request(width, height)
        self._web_view.set_full_content_zoom(True)
        self._web_view.load_uri(uri)
        self._attach(self._web_view)
        self._web_view.show()
        return self._web_view

    def set_zoom_level(self, zoom_level):
        if self._web_view is not None:
            self._web_view.set_zoom_level(zoom_level)

    def add_entry(self, text=''):
        entry = Gtk.Entry()
        offset = style.GRID_CELL_SIZE
        entry.set_size_request(offset * 8, -1)
        entry.set_text(text)
        self._attach(entry)
        entry.show()
        return entry

    def add_image(self, image):
        image = Gtk.Image.new_from_file(image)
        self._attach(image)
        image.show()

    def add_two_images(self, left_image, right_image):
        image_boxes = [Gtk.Alignment.new(0.5, 0, 0, 0),
                       Gtk.Alignment.new(0.5, 0, 0, 0)]
        left = Gtk.Image.new_from_file(left_image)
        right = Gtk.Image.new_from_file(right_image)
        image_boxes[0].add(left)
        left.show()
        image_boxes[1].add(right)
        right.show()
        self._attach_two(image_boxes[0], image_boxes[1])
        image_boxes[0].show()
        image_boxes[1].show()
        return image_boxes

    def add_button(self, button_label, callback, arg=None, button_icon=None):
        if button_icon is not None:
            button = ToolButton(button_icon)
        else:
            button = Gtk.Button()
            button.set_label(button_label)
        self._attach_center(button)
        if callback is not None:
            if arg is None:
                button.connect('clicked', callback)
            else:
                button.connect('clicked', callback, arg)
        button.show()
        return button

    def add_yes_no_buttons(self, callback):
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(style.DEFAULT_SPACING * 2)
        grid.set_column_homogeneous(True)
        yesbutton = Gtk.Button()
        yesbutton.set_label(_('Yes'))
        nobutton = Gtk.Button()
        nobutton.set_label(_('No'))
        grid.attach(yesbutton, 0, 0, 1, 1)
        yesbutton.connect('clicked', callback, 'yes')
        yesbutton.show()
        grid.attach(nobutton, 1, 0, 1, 1)
        nobutton.connect('clicked', callback, 'no')
        nobutton.show()
        self._attach_center(grid)
        grid.show()
        return [yesbutton, nobutton]

    def add_radio_buttons(self, button_icons, colors=None):
        # Psuedo-radio buttons
        alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(style.DEFAULT_SPACING * 2)
        buttons = []
        for i, button_icon in enumerate(button_icons):
            if i == 0:
                group = None
            else:
                group = buttons[0]

            if colors is not None:
                icon = Icon(pixel_size=style.STANDARD_ICON_SIZE,
                            icon_name=button_icon,
                            stroke_color=colors.get_stroke_color(),
                            fill_color=colors.get_fill_color())
            else:
                icon = Icon(pixel_size=style.STANDARD_ICON_SIZE,
                            icon_name=button_icon)

            buttons.append(Gtk.Button())
            buttons[i].set_image(icon)
            grid.attach(buttons[i], i, 0, 1, 1)
            buttons[i].show()
        alignment.add(grid)
        grid.show()
        self._attach(alignment)
        alignment.show()

        return buttons
