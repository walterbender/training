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

from gi.repository import Gtk, Gdk, GConf
import dbus

from sugar3.activity import activity
from sugar3 import profile
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.objectchooser import ObjectChooser
from sugar3.graphics.colorbutton import ColorToolButton
from sugar3.graphics.alert import NotifyAlert

from toolbar_utils import button_factory, separator_factory

from gettext import gettext as _

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

        self.nick = profile.get_nick_name()

        self._setup_toolbars()

        # Create a canvas
        canvas = Gtk.DrawingArea()
        canvas.set_size_request(Gdk.Screen.width(), \
                                Gdk.Screen.height())
        self.set_canvas(canvas)
        canvas.show()
        self.show_all()

        self.current_task = 0
        if 'current task' in self.metadata:
            self.current_task = int(self.metadata['current task'])
            _logger.debug('reading current task from metadata')
            _logger.debug(self.current_task)

        self._exercises = Exercises(canvas, parent=self)
        _logger.debug('starting execises at %d' % self.current_task)
        self._exercises.task_master()
        _logger.debug('finishing execises at %d' % self.current_task)

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
	alert.connect('response', _task_alert_response_cb, self)
	self.add_alert(alert)
	alert.show()

    def write_file(self, file_path):
        self.metadata['current task'] = self.current_task

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
