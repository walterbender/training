# -*- coding: utf-8 -*-
#Copyright (c) 2013 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

from gi.repository import Gtk, Gdk, GConf, GObject
import dbus
import os
from shutil import copy
import json
from gettext import gettext as _

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbutton import ToolButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.objectchooser import ObjectChooser
from sugar3.graphics.colorbutton import ColorToolButton
from sugar3.graphics.alert import NotifyAlert
from sugar3.graphics import style
from sugar3.graphics.icon import Icon

from toolbar_utils import button_factory, separator_factory
from exercises import Exercises

import logging
_logger = logging.getLogger('training-activity')


class TrainingActivity(activity.Activity):
    ''' A series of training exercises '''

    def __init__(self, handle):
        ''' Initialize the toolbars and the game board '''
        try:
            super(TrainingActivity, self).__init__(handle)
        except dbus.exceptions.DBusException, e:
            _logger.error(str(e))

        self._setup_toolbars()

        self.prompt_label = Gtk.Label(
            '<span foreground="%s"><b>%s</b></span>' %
            (style.COLOR_BUTTON_GREY.get_html(), _('Sugar Training Activity')))

        self.current_task = self.read_task_data('current_task')
        if self.current_task is None:
            self.current_task = 0
            self.button_label = Gtk.Label(_('Begin'))
        else:
            _logger.debug(self.current_task)
            self.button_label = Gtk.Label(_('Resume'))

        self.empty_widgets = Gtk.EventBox()
        self.show_prompt('training-trophy', self._prompt_cb)

        self.show_all()

        self._exercises = Exercises(self)

    def _prompt_cb(self, button):
        self._exercises.task_master()

    def __stop_clicked_cb(self, button):
        self.destroy()

    def __ok_clicked_cb(self, button):
        self.destroy()

    def alert_task(self, title=None, msg=None):
        alert = NotifyAlert()
        if title is None:
            alert.props.title = _('Your task, should you choose to accept it')
        else:
            alert.props.title = title
        if msg is None:
            alert.props.msg = '---'
        else:
            alert.props.msg = msg

	def _task_alert_response_cb(alert, response_id, self):
            self.remove_alert(alert)
            if not self._exercises.completed:
                self._exercises.task_master()
            else:
                self.close()

	alert.connect('response', _task_alert_response_cb, self)
	self.add_alert(alert)
	alert.show()

    def write_file(self, file_path):
        self.write_task_data('current_task', self.current_task)

    def _setup_toolbars(self):
	''' Setup the toolbars. '''

	self.max_participants = 1  # No sharing

        toolbox = ToolbarBox()
        # Activity toolbar
        activity_button = ActivityToolbarButton(self)
        toolbox.toolbar.insert(activity_button, 0)
        activity_button.show()

        self.set_toolbar_box(toolbox)
        toolbox.show()
        self.toolbar = toolbox.toolbar

        separator_factory(toolbox.toolbar, True, False)
        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def show_prompt(self, icon_name, btn_callback):
        self.empty_widgets.modify_bg(Gtk.StateType.NORMAL,
                                     style.COLOR_WHITE.get_gdk_color())

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        mvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(mvbox, True, False, 0)

        image_icon = Icon(pixel_size=style.LARGE_ICON_SIZE,
                          icon_name=icon_name,
                          stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                          fill_color=style.COLOR_TRANSPARENT.get_svg())
        mvbox.pack_start(image_icon, False, False, style.DEFAULT_PADDING)

        self.prompt_label.set_use_markup(True)
        mvbox.pack_start(self.prompt_label, False, False,
                         style.DEFAULT_PADDING)

        hbox = Gtk.Box()
        open_image_btn = Gtk.Button()
        open_image_btn.connect('clicked', btn_callback)
        add_image = Gtk.Image.new_from_stock(Gtk.STOCK_ADD,
                                             Gtk.IconSize.BUTTON)
        buttonbox = Gtk.Box()
        buttonbox.pack_start(add_image, False, True, 0)
        buttonbox.pack_end(self.button_label, True, True, 5)
        open_image_btn.add(buttonbox)
        hbox.pack_start(open_image_btn, True, False, 0)
        mvbox.pack_start(hbox, False, False, style.DEFAULT_PADDING)

        self.empty_widgets.add(vbox)
        self.empty_widgets.show_all()
        self.set_canvas(self.empty_widgets)

    def add_badge(self, msg, icon="training-trophy", name="Sugar"):
        badge = {
            'icon': icon,
            'from': name,
            'message': msg
        }
        icon_path = os.path.join(activity.get_bundle_path(),
                                 'icons',
                                 (icon + '.svg'))
        sugar_icons = os.path.join(os.path.expanduser('~'), '.icons')
        copy(icon_path, sugar_icons)

        if 'comments' in self.metadata:
            comments = json.loads(self.metadata['comments'])
            comments.append(badge)
            self.metadata['comments'] = json.dumps(comments)
        else:
            self.metadata['comments'] = json.dumps([badge])

    def read_task_data(self, uid):
        data_path = os.path.join(self.get_activity_root(), 'data',
                                 'training_data')
        uid_data = None
        if os.path.exists(data_path):
            fd = open(data_path, 'r')
            json_data = fd.read()
            fd.close()
            data = json.loads(json_data)
            if uid in data:
                uid_data = data[uid]
        return uid_data

    def write_task_data(self, uid, uid_data):
        data_path = os.path.join(self.get_activity_root(), 'data',
                                 'training_data')
        data = {}
        if os.path.exists(data_path):
            fd = open(data_path, 'r')
            json_data = fd.read()
            fd.close()
            data = json.loads(json_data)
        data[uid] = uid_data
        json_data = json.dumps(data)
        fd = open(data_path, 'w')
        fd.write(json_data)
        fd.close()

