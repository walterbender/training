# -*- coding: utf-8 -*-
#Copyright (c) 2013,14 Walter Bender

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
import dbus
import os
from shutil import copy
import json
from gettext import gettext as _

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics import style

from jarabe.view.viewhelp import ViewHelp

from toolbar_utils import separator_factory, label_factory, button_factory
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

        self.connect('realize', self.__realize_cb)
        self._overall_progress = 0

        self._setup_toolbars()

        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self._exercises = Exercises(self)

        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        center_in_panel.add(self._exercises)
        self._exercises.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

        self.completed = False
        self._exercises.task_master()

    def write_file(self, file_path):
        self._exercises.write_task_data('current_task',
                                        self._exercises.current_task)

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

        self.help_button = button_factory('toolbar-help',
            toolbox.toolbar, self._help_cb, tooltip=_('help'),
            accelerator=_('<Ctrl>H'))
        self.help_button.set_sensitive(False)

        self.progress_label = label_factory(toolbox.toolbar, '', width=200)
        self.progress_label.set_use_markup(True)

        separator_factory(toolbox.toolbar, True, False)
        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def __realize_cb(self, window):
        self.window_xid = window.get_window().get_xid()

    def _help_cb(self, button):
        title, help_file = self._exercises.get_help_info()
        _logger.debug('%s: %s' % (title, help_file))
        if not hasattr(self, 'window_xid'):
            self.window_xid = self.get_window().get_xid()
        if title is not None and help_file is not None:
            self.viewhelp = ViewHelp(title, help_file, self.window_xid)
            self.viewhelp.show()

    def add_badge(self, msg, icon="training-trophy", name="One Academy"):
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

