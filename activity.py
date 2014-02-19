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

import dbus
import os
import json
import subprocess
from ConfigParser import ConfigParser
from gettext import gettext as _

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from sugar3.activity import activity
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics.alert import ConfirmationAlert
from sugar3.graphics import style

try:
    from jarabe.webservice import account
    WEBSERVICES_AVAILABLE = True
except:
    WEBSERVICES_AVAILABLE = False

NAME_UID = 'name'
EMAIL_UID = 'email_address'
SCHOOL_UID = 'school_name'
TRAINING_DATA_UID = 'training_data_uid'
VERSION_NUMBER = 'version_number'
COMPLETION_PERCENTAGE = 'completion_percentage'
TRAINING_DATA_EMAIL = 'training_data_email'
TRAINING_DATA_FULLNAME = 'training_data_fullname'

from toolbar_utils import (separator_factory, label_factory, button_factory,
                           radio_factory)
from taskmaster import TaskMaster
from graphics import Graphics, FONT_SIZES
# from checkprogress import CheckProgress
from helppanel import HelpPanel
import utils
from power import get_power_manager

import logging
_logger = logging.getLogger('training-activity')


_MINIMUM_SPACE = 1024 * 1024 * 10  # 10MB is very conservative
_REQUIRED_SUGARSERVICES_VERSION = 5


def _check_gconf_settings():
    from gi.repository import GConf

    client = GConf.Client.get_default()
    # url = client.get_string('/desktop/sugar/services/training/url')
    client.set_string(
        '/desktop/sugar/services/training/url',
        'https://training.one-education.org/training/report ')
    # api_key = client.get_string('/desktop/sugar/services/training/api_key')
    client.set_string('/desktop/sugar/services/training/api_key',
                      'SbCeK4nH8dpQJsHNn9djza9g')


class TrainingActivity(activity.Activity):
    ''' A series of training exercises '''
    transfer_started_signal = GObject.Signal('started', arg_types=([]))
    transfer_progressed_signal = GObject.Signal('progressed', arg_types=([]))
    transfer_completed_signal = GObject.Signal('completed', arg_types=([]))
    transfer_failed_signal = GObject.Signal('failed', arg_types=([]))

    def __init__(self, handle):
        ''' Initialize the toolbars and the game board '''
        try:
            super(TrainingActivity, self).__init__(handle)
        except dbus.exceptions.DBusException, e:
            _logger.error(str(e))

        self.connect('realize', self.__realize_cb)
        self.connect('started', self.__transfer_started_cb)
        self.connect('progressed', self.__transfer_progressed_cb)
        self.connect('completed', self.__transfer_completed_cb)
        self.connect('failed', self.__transfer_failed_cb)

        self.volume_monitor = Gio.VolumeMonitor.get()
        self.volume_monitor.connect('mount-added', self._mount_added_cb)
        self.volume_monitor.connect('mount-removed', self._mount_removed_cb)

        if hasattr(self, 'metadata') and 'font_size' in self.metadata:
            self.font_size = int(self.metadata['font_size'])
        else:
            self.font_size = 8
        self.zoom_level = self.font_size / float(len(FONT_SIZES))
        _logger.debug('zoom level is %f' % self.zoom_level)

        _check_gconf_settings()  # For debugging purposes

        self._setup_toolbars()
        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self.bundle_path = activity.get_bundle_path()
        self.volume_data = []

        self._copy_entry = None
        self._paste_entry = None
        self._webkit = None
        self.help_palette = None
        self._clipboard_text = ''

        if self._load_extension() and self.check_volume_data():
            self._launcher()

    def _launcher(self):
        get_power_manager().inhibit_suspend()

        # We are resuming the activity or we are launching a new instance?
        # * Is there a data file to sync on the USB key?
        # * Do we create a new data file on the USB key?
        path = self._check_for_USB_data()
        if path is None:
            self._launch_task_master()
        elif self._sync_data_from_USB(path):
            self._copy_data_from_USB()
            # Flash a welcome back screen.
            self._load_intro_graphics(file_name='welcome-back.html')
            GObject.timeout_add(1500, self._launch_task_master)

    def can_close(self):
        get_power_manager().restore_suspend()
        return True

    def check_volume_data(self):
        # Before we begin (and before each task),
        # we need to find any and all USB keys
        # and any and all training-data files on them.

        _logger.debug(utils.get_volume_paths())
        self.volume_data = []
        for path in utils.get_volume_paths():
            os.path.basename(path)
            self.volume_data.append(
                {'basename': os.path.basename(path),
                 'files': utils.look_for_training_data(path),
                 'sugar_path': os.path.join(self.get_activity_root(), 'data'),
                 'usb_path': path})
            _logger.debug(self.volume_data[-1])

        # (1) We require a USB key
        if len(self.volume_data) == 0:
            _logger.error('NO USB KEY INSERTED')
            alert = ConfirmationAlert()
            alert.props.title = _('USB key required')
            alert.props.msg = _('You must insert a USB key before launching '
                                'this activity.')
            alert.connect('response', self._remove_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(file_name='insert-usb.html')
            return False

        # (2) Only one USB key
        if len(self.volume_data) > 1:
            _logger.error('MULTIPLE USB KEYS INSERTED')
            alert = ConfirmationAlert()
            alert.props.title = _('Multiple USB keys found')
            alert.props.msg = _('Only one USB key must be inserted while '
                                'running this program.\nPlease remove any '
                                'additional USB keys before launching '
                                'this activity.')
            alert.connect('response', self._remove_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)
            return False

        volume = self.volume_data[0]

        # (3) At least 10MB of free space
        if utils.is_full(volume['usb_path'],
                         required=_MINIMUM_SPACE):
            _logger.error('USB IS FULL')
            alert = ConfirmationAlert()
            alert.props.title = _('USB key is full')
            alert.props.msg = _('No room on USB')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)
            return False

        # (4) File is read/write
        if not utils.is_writeable(volume['usb_path']):
            _logger.error('CANNOT WRITE TO USB')
            alert = ConfirmationAlert()
            alert.props.title = _('Cannot write to USB')
            alert.props.msg = _('USB key seems to be read-only.')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)
            return False

        # (5) Only one set of training data per USB key
        # We expect UIDs to formated as XXXX-XXXX
        # We need to make sure we have proper UIDs associated with
        # the USBs and the files on them match the UID.
        # (a) If there are no files, we will assign the UID based on the
        #     volume path;
        # (b) If there is one file with a valid UID, we use that UID;
        if len(volume['files']) == 0:
            volume['uid'] = 'training-data-%s' % \
                            utils.format_volume_name(volume['basename'])
            _logger.debug('No training data found. Using UID %s' %
                          volume['uid'])
            return True
        elif len(volume['files']) == 1:
            volume['uid'] = 'training-data-%s' % volume['files'][0][-9:]
            _logger.debug('Training data found. Using UID %s' %
                          volume['uid'])
            return True
        else:
            _logger.error('MULTIPLE TRAINING-DATA FILES FOUND')
            alert = ConfirmationAlert()
            alert.props.title = _('Multiple training-data files found.')
            alert.props.msg = _('There can only be one set of training '
                                'data per USB key.')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)
            return False

    def _check_for_USB_data(self):
        usb_path = os.path.join(self.volume_data[0]['usb_path'],
                                self.volume_data[0]['uid'])
        if os.path.exists(usb_path):
            return usb_path
        else:
            return None

    def _sync_data_from_USB(self, usb_data_path=None):
        # We need to sync up file on USB with file on disk,
        # but only if the email addresses match. Otherwise,
        # raise an error.
        if usb_data_path is not None:
            usb_data = {}
            if os.path.exists(usb_data_path):
                fd = open(usb_data_path, 'r')
                json_data = fd.read()
                fd.close()
                if len(json_data) > 0:
                    try:
                        usb_data = json.loads(json_data)
                    except ValueError, e:
                        _logger.error('Cannot load USB data: %s' % e)
            else:
                _logger.error('Cannot find USB data: %s' % usb_data_path)

            sugar_data_path = os.path.join(
                self.volume_data[0]['sugar_path'],
                self.volume_data[0]['uid'])
            sugar_data = {}
            if os.path.exists(sugar_data_path):
                fd = open(sugar_data_path, 'r')
                json_data = fd.read()
                fd.close()
                if len(json_data) > 0:
                    try:
                        sugar_data = json.loads(json_data)
                    except ValueError, e:
                        _logger.error('Cannot load Sugar data: %s' % e)
            else:
                _logger.error('Cannot find Sugar data: %s' % sugar_data_path)

            # First, check to make sure email_address matches
            if EMAIL_UID in usb_data:
                usb_email = usb_data[EMAIL_UID]
            else:
                usb_email = None
            if EMAIL_UID in sugar_data:
                sugar_email = sugar_data[EMAIL_UID]
            else:
                sugar_email = None
            if usb_email != sugar_email:
                if usb_email is None and sugar_email is not None:
                    _logger.warning('Using email address from Sugar: %s' %
                                    sugar_email)
                    usb_data[EMAIL_UID] = sugar_email
                elif usb_email is not None and sugar_email is None:
                    _logger.warning('Using email address from USB: %s' %
                                    usb_email)
                    sugar_data[EMAIL_UID] = usb_email
                elif usb_email is None and sugar_email is None:
                    _logger.warning('No email address found')
                else:
                    # FIX ME: We need to resolve this, but for right now, punt.
                    alert = ConfirmationAlert()
                    alert.props.title = _('Data mismatch')
                    alert.props.msg = _('Are you %(usb)s or %(sugar)s?' %
                                        {'usb': usb_email,
                                         'sugar': sugar_email})
                    alert.connect('response', self._close_alert_cb)
                    self.add_alert(alert)
                    self._load_intro_graphics(message=alert.props.msg)
                    return False

            def count_completed(data):
                count = 0
                for key in data:
                    if isinstance(data[key], dict) and \
                       'completed' in data[key] and \
                       data[key]['completed']:
                        count += 1
                return count

            # The database with the most completed tasks takes precedence.
            if count_completed(usb_data) >= count_completed(sugar_data):
                _logger.debug('data sync: USB data takes precedence')
                data_one = usb_data
                data_two = sugar_data
            else:
                _logger.debug('data sync: Sugar data takes precedence')
                data_one = sugar_data
                data_two = usb_data

            # Copy completed tasks from one to two
            for key in data_one:
                if isinstance(data_one[key], dict) and \
                   'completed' in data_one[key] and \
                   data_one[key]['completed']:
                    data_two[key] = data_one[key]

            # Copy completed tasks from two to one
            for key in data_two:
                if isinstance(data_two[key], dict) and \
                   'completed' in data_two[key] and \
                   data_two[key]['completed']:
                    data_one[key] = data_two[key]

            # Copy incompleted tasks from one to two
            for key in data_one:
                if isinstance(data_one[key], dict) and \
                   (not 'completed' in data_one[key] or
                    not data_one[key]['completed']):
                        data_two[key] = data_one[key]

            # Copy incompleted tasks from two to one
            for key in data_two:
                if isinstance(data_two[key], dict) and \
                   (not 'completed' in data_two[key] or
                    not data_two[key]['completed']):
                        data_one[key] = data_two[key]

            # Copy name, email_address, current_task...
            for key in data_one:
                if not isinstance(data_one[key], dict):
                    data_two[key] = data_one[key]
            for key in data_two:
                if not isinstance(data_two[key], dict):
                    data_one[key] = data_two[key]

            # Finally, write to the USB and ...
            json_data = json.dumps(data_one)
            fd = open(usb_data_path, 'w')
            fd.write(json_data)
            fd.close()

            # ...save a shadow copy in Sugar
            fd = open(sugar_data_path, 'w')
            fd.write(json_data)
            fd.close()
            return True
        else:
            _logger.error('No data to sync on USB')
            return False

    def _copy_data_from_USB(self):
        usb_path = self._check_for_USB_data()
        if usb_path is not None:
            try:
                subprocess.call(['cp', usb_path,
                                 self.volume_data[0]['sugar_path']])
            except OSError, e:
                _logger.error('Could not copy %s to %s: %s' % (
                    usb_path, self.volume_data[0]['sugar_path'], e))
        else:
            _logger.error('No data found on USB')

    def toolbar_expanded(self):
        if self.activity_button.is_expanded():
            return True
        elif self.edit_toolbar_button.is_expanded():
            return True
        elif self.view_toolbar_button.is_expanded():
            return True
        elif hasattr(self, 'progress_toolbar_button') and \
             self.progress_toolbar_button.is_expanded():
            return True

    def _launch_task_master(self):
        self.check_progress = None

        # We need a box whose size will change when the toolbars are expanded
        self._fixed = Gtk.Fixed()
        self._fixed.set_size_request(Gdk.Screen.width(), Gdk.Screen.height())
        self.set_canvas(self._fixed)
        self._fixed.show()

        # Offsets from the bottom of the screen
        dy1 = 3 * style.GRID_CELL_SIZE
        dy2 = 2 * style.GRID_CELL_SIZE

        self._progress_area = Gtk.Alignment.new(0.5, 0, 0, 0)
        self._progress_area.set_size_request(Gdk.Screen.width(), -1)
        self._fixed.put(self._progress_area, 0, Gdk.Screen.height() - dy2)
        self._progress_area.show()

        self._button_area = Gtk.Alignment.new(0.5, 0, 0, 0)
        self._button_area.set_size_request(Gdk.Screen.width(), -1)
        self._fixed.put(self._button_area, 0, Gdk.Screen.height() - dy1)
        self._button_area.show()

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_size_request(
            Gdk.Screen.width(), Gdk.Screen.height() - dy1)
        self._scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                         Gtk.PolicyType.AUTOMATIC)

        self._graphics_area = Gtk.Alignment.new(0.5, 0, 0, 0)
        self._scrolled_window.add_with_viewport(self._graphics_area)
        self._graphics_area.show()
        self._fixed.put(self._scrolled_window, 0, 0)
        self._scrolled_window.show()

        self._task_master = TaskMaster(self)
        self._task_master.show()

        # Now that we have the tasks, we can build the progress toolbar and
        # help panel.
        self._build_progress_toolbar()
        self._help_panel = HelpPanel(self._task_master)
        self.help_palette = self._help_button.get_palette()
        self.help_palette.set_content(self._help_panel)
        self._help_panel.show()
        self._help_button.set_sensitive(True)

        Gdk.Screen.get_default().connect('size-changed', self._configure_cb)
        self._toolbox.connect('hide', self._resize_hide_cb)
        self._toolbox.connect('show', self._resize_show_cb)

        self._task_master.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self._task_master.connect('key_press_event',
                                  self._task_master.keypress_cb)
        self._task_master.set_can_focus(True)
        self._task_master.grab_focus()

        self.completed = False
        self._task_master.task_master()

    def load_graphics_area(self, widget):
        self._graphics_area.add(widget)

    def load_button_area(self, widget):
        self._button_area.add(widget)

    def load_progress_area(self, widget):
        self._progress_area.add(widget)

    def _load_intro_graphics(self, file_name='generic-problem.html',
                             message=None):
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        url = os.path.join(self.bundle_path, 'html-content', file_name)
        graphics = Graphics()
        if message is None:
            graphics.add_uri('file://' + url)
        else:
            graphics.add_uri('file://' + url + '?MSG=' +
                             utils.get_safe_text(message))
        graphics.set_zoom_level(0.667)
        center_in_panel.add(graphics)
        graphics.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

    def _resize_hide_cb(self, widget):
        self._resize_canvas(widget, True)

    def _resize_show_cb(self, widget):
        self._resize_canvas(widget, False)

    def _configure_cb(self, event):
        self._fixed.set_size_request(Gdk.Screen.width(), Gdk.Screen.height())
        if Gdk.Screen.width() > Gdk.Screen.height():
            self._scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                             Gtk.PolicyType.AUTOMATIC)
        else:
            self._scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                             Gtk.PolicyType.AUTOMATIC)
        self._resize_canvas(None)
        self._task_master.reload_graphics()

    def _resize_canvas(self, widget, fullscreen=False):
        # When a toolbar is expanded or collapsed, resize the canvas
        # to ensure that the progress bar is still visible.
        if hasattr(self, '_task_master'):
            if self.toolbar_expanded():
                dy1 = 4 * style.GRID_CELL_SIZE
                dy2 = 3 * style.GRID_CELL_SIZE
            else:
                dy1 = 3 * style.GRID_CELL_SIZE
                dy2 = 2 * style.GRID_CELL_SIZE

            if fullscreen:
                dy1 -= 2 * style.GRID_CELL_SIZE
                dy2 -= 2 * style.GRID_CELL_SIZE

            self._scrolled_window.set_size_request(
                Gdk.Screen.width(), Gdk.Screen.height() - dy1)
            self._fixed.put(self._progress_area, 0, Gdk.Screen.height() - dy2)
            self._fixed.put(self._button_area, 0, Gdk.Screen.height() - dy1)

    def get_activity_version(self):
        info_path = os.path.join(self.bundle_path, 'activity', 'activity.info')
        try:
            info_file = open(info_path, 'r')
        except Exception, e:
            _logger.error('Could not open %s: %s' % (info_path, e))
            return 'unknown'

        cp = ConfigParser()
        cp.readfp(info_file)

        section = 'Activity'

        if cp.has_option(section, 'activity_version'):
            activity_version = cp.get(section, 'activity_version')
        else:
            activity_version = 'unknown'
        return activity_version

    def get_uid(self):
        if len(self.volume_data) == 1:
            return self.volume_data[0]['uid']
        else:
            return 'unknown'

    def write_file(self, file_path):
        # Only write if we have a valid USB/data file to work with.
        if len(self.volume_data) == 1 and \
           len(self.volume_data[0]['files']) == 1:
            self.metadata[TRAINING_DATA_UID] = self.volume_data[0]['uid']

            # We may have failed before getting to init of taskmaster
            if hasattr(self, '_task_master'):
                self._task_master.write_task_data(
                    'current_task', self._task_master.current_task)
                self.update_activity_title()
                email = self._task_master.read_task_data(EMAIL_UID)
                if email is None:
                    email = ''
                self.metadata[TRAINING_DATA_EMAIL] = email
                name = self._task_master.read_task_data(NAME_UID)
                if name is None:
                    name = ''
                self.metadata[TRAINING_DATA_FULLNAME] = name

        self.metadata['font_size'] = str(self.font_size)

    def update_activity_title(self):
        name = self._task_master.read_task_data(NAME_UID)
        if name is not None:
            bundle_name = activity.get_bundle_name()
            self.metadata['title'] = _('%(name)s %(bundle)s Activity') % \
                {'name': name, 'bundle': bundle_name}

    def _setup_toolbars(self):
        ''' Setup the toolbars. '''
        self.max_participants = 1  # No sharing

        self._toolbox = ToolbarBox()

        self.activity_button = ActivityToolbarButton(self)
        self.activity_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        self.set_toolbar_box(self._toolbox)
        self._toolbox.show()
        self.toolbar = self._toolbox.toolbar

        view_toolbar = Gtk.Toolbar()
        self.view_toolbar_button = ToolbarButton(
            page=view_toolbar,
            label=_('View'),
            icon_name='toolbar-view')
        self.view_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.view_toolbar_button, 1)
        view_toolbar.show()
        self.view_toolbar_button.show()

        button_factory('view-fullscreen', view_toolbar,
                       self._fullscreen_cb, tooltip=_('Fullscreen'),
                       accelerator='<Alt>Return')

        self._zoom_in = button_factory('zoom-in',  # 'resize+',
                                       view_toolbar,
                                       self._zoom_in_cb,
                                       tooltip=_('Increase font size'))

        self._zoom_out = button_factory('zoom-out',  # 'resize-',
                                        view_toolbar,
                                        self._zoom_out_cb,
                                        tooltip=_('Decrease font size'))
        self._set_zoom_buttons_sensitivity()

        edit_toolbar = Gtk.Toolbar()
        self.edit_toolbar_button = ToolbarButton(
            page=edit_toolbar,
            label=_('Edit'),
            icon_name='toolbar-edit')
        self.edit_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.edit_toolbar_button, 1)
        edit_toolbar.show()
        self.edit_toolbar_button.show()

        self._copy_button = button_factory('edit-copy', edit_toolbar,
                                           self._copy_cb, tooltip=_('Copy'),
                                           accelerator='<Ctrl>C')
        self._copy_button.set_sensitive(False)

        self._paste_button = button_factory('edit-paste', edit_toolbar,
                                            self._paste_cb, tooltip=_('Paste'),
                                            accelerator='<Ctrl>V')
        self._paste_button.set_sensitive(False)

        self._help_button = button_factory('toolbar-help',
                                           self._toolbox.toolbar,
                                           self._help_cb, tooltip=_('help'),
                                           accelerator=_('<Ctrl>H'))
        self._help_button.set_sensitive(False)

        '''
        button_factory('check-progress',
                       self._toolbox.toolbar,
                       self._check_progress_cb,
                       tooltip=_('Check progress'))
        '''

        self.transfer_button = button_factory(
            'transfer',
            self._toolbox.toolbar,
            self._transfer_cb,
            tooltip=_('Training data upload status'))
        self.transfer_button.hide()

        self.progress_label = label_factory(self._toolbox.toolbar, '',
                                            width=300)
        self.progress_label.set_use_markup(True)

        separator_factory(self._toolbox.toolbar, True, False)
        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        self._toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def _build_progress_toolbar(self):
        progress_toolbar = Gtk.Toolbar()
        self.progress_toolbar_button = ToolbarButton(
            page=progress_toolbar,
            label=_('Check progress'),
            icon_name='check-progress')
        self.progress_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.progress_toolbar_button, 3)
        progress_toolbar.show()
        self.progress_toolbar_button.show()

        self._progress_buttons = []
        progress = self._task_master.get_completed_sections()

        for section in range(self._task_master.get_number_of_sections()):
            icon = self._task_master.get_section_icon(section)
            if section in progress:
                icon = icon + '-white'
            else:
                icon = icon + '-grey'

            name = self._task_master.get_section_name(section)

            if section == 0:
                group = None
            else:
                group = self._progress_buttons[0]

            self._progress_buttons.append(
                radio_factory(icon,
                              progress_toolbar,
                              self._jump_to_section_cb,
                              cb_arg=section,
                              tooltip=name,
                              group=group))
            self._progress_buttons[section].show()

        self._radio_buttons_live = False
        section, task = self._task_master.get_section_and_task_index()
        self._progress_buttons[section].set_active(True)
        self._radio_buttons_live = True

    def mark_section_as_complete(self, section):
        icon = self._task_master.get_section_icon(section) + '-white'
        self._progress_buttons[section].set_icon_name(icon)
        if section < self._task_master.get_number_of_sections() - 1:
            self._radio_buttons_live = False
            self._progress_buttons[section + 1].set_active(True)
            self._radio_buttons_live = True

    def _transfer_cb(self, button):
        ''' Hide the button to dismiss notification '''
        self.transfer_button.set_tooltip(_('Training data upload status'))
        self.transfer_button.hide()

    def __transfer_started_cb(self, widget):
        self.transfer_button.set_icon_name('transfer')
        self.transfer_button.set_tooltip(_('Data transfer started'))
        self.transfer_button.show()

    def __transfer_progressed_cb(self, widget):
        self.transfer_button.set_tooltip(_('Data transfer progressing'))
        self.transfer_button.show()

    def __transfer_completed_cb(self, widget):
        self.transfer_button.set_icon_name('transfer-complete')
        self.transfer_button.set_tooltip(_('Data transfer completed'))
        self.transfer_button.show()

    def __transfer_failed_cb(self, widget):
        self.transfer_button.set_icon_name('transfer-failed')
        self.transfer_button.set_tooltip(_('Data transfer failed'))
        self.transfer_button.show()

    def __realize_cb(self, window):
        self.window_xid = window.get_window().get_xid()

    def set_copy_widget(self, webkit=None, text_entry=None):
        # Each task is responsible for setting a widget for copy
        if webkit is not None:
            self._webkit = webkit
        else:
            self._webkit = None
        if text_entry is not None:
            self._copy_entry = text_entry
        else:
            self._copy_entry = None

        self._copy_button.set_sensitive(webkit is not None or
                                        text_entry is not None)

    def _copy_cb(self, button):
        if self._copy_entry is not None:
            self._copy_entry.copy_clipboard()
        elif self._webkit is not None:
            self._webkit.copy_clipboard()
        else:
            _logger.debug('No widget set for copy.')

    def set_paste_widget(self, text_entry=None):
        # Each task is responsible for setting a widget for paste
        if text_entry is not None:
            self._paste_entry = text_entry
        self._paste_button.set_sensitive(text_entry is not None)

    def _paste_cb(self, button):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard_text = clipboard.wait_for_text()
        if self._paste_entry is not None:
            self._paste_entry.paste_clipboard()
        else:
            _logger.debug('No widget set for paste (%s).' %
                          self.clipboard_text)

    def _fullscreen_cb(self, button):
        ''' Hide the Sugar toolbars. '''
        self.fullscreen()

    def _set_zoom_buttons_sensitivity(self):
        if self.font_size < len(FONT_SIZES) - 1:
            self._zoom_in.set_sensitive(True)
        else:
            self._zoom_in.set_sensitive(False)
        if self.font_size > 0:
            self._zoom_out.set_sensitive(True)
        else:
            self._zoom_out.set_sensitive(False)

    def _zoom_in_cb(self, button):
        if self.font_size < len(FONT_SIZES) - 1:
            self.font_size += 1
            self.zoom_level *= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _zoom_out_cb(self, button):
        if self.font_size > 0:
            self.font_size -= 1
            self.zoom_level /= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _jump_to_section_cb(self, button, section):
        # def _check_progress_cb(self, button, section):
        # self.check_progress = CheckProgress(self._task_master)
        # self._task_master.load_progress_summary(self.check_progress)
        if self._radio_buttons_live:
            uid = self._task_master.section_and_task_to_uid(section)
            self._task_master.current_task = \
                self._task_master.uid_to_task_number(uid)
            self._task_master.reload_graphics()

    def _help_cb(self, button):
        # title, help_file = self._task_master.get_help_info()
        # _logger.debug('%s: %s' % (title, help_file))
        # if not hasattr(self, 'window_xid'):
        #    self.window_xid = self.get_window().get_xid()
        # if title is not None and help_file is not None:
        #     self.viewhelp = ViewHelp(title, help_file, self.window_xid)
        #     self.viewhelp.show()
        try:
            self._help_panel.set_connected(
                utils.nm_status() == 'network-wireless-connected')
        except Exception, e:
            _logger.error('Could not read NM status: %s' % (e))
            self._help_panel.set_connected(False)

        if self.help_palette:
            if not self.help_palette.is_up():
                self.help_palette.popup(
                    immediate=True,
                    state=self.help_palette.SECONDARY)
            else:
                self.help_palette.popdown(immediate=True)
            return

    def add_badge(self, msg, icon="training-trophy", name="One Academy"):
        sugar_icons = os.path.join(os.path.expanduser('~'), '.icons')
        if not os.path.exists(sugar_icons):
            try:
                subprocess.call(['mkdir', sugar_icons])
            except OSError, e:
                _logger.error('Could not mkdir %s, %s' % (sugar_icons, e))

        badge = {
            'icon': icon,
            'from': name,
            'message': msg
        }

        # Use icons from html-content directory since default colors are
        # intended for white background.
        icon_dir = os.path.join(self.bundle_path, 'html-content', 'images')
        icon_path = os.path.join(icon_dir, icon + '.svg')
        try:
            subprocess.call(['cp', icon_path, sugar_icons])
        except OSError, e:
            _logger.error('Could not copy %s to %s, %s' %
                          (icon_path, sugar_icons, e))

        if 'comments' in self.metadata:
            comments = json.loads(self.metadata['comments'])
            comments.append(badge)
            self.metadata['comments'] = json.dumps(comments)
        else:
            self.metadata['comments'] = json.dumps([badge])

    def _load_extension(self):
        if not WEBSERVICES_AVAILABLE:
            _logger.error('Webservices not available on this version of Sugar')
            self._webservice_alert(_('Sugar upgrade required.'))
            return False

        extensions_path = os.path.join(os.path.expanduser('~'), '.sugar',
                                       'default', 'extensions')
        webservice_path = os.path.join(extensions_path, 'webservice')
        sugarservices_path = os.path.join(self.bundle_path, 'sugarservices')
        init_path = os.path.join(self.bundle_path, 'sugarservices',
                                 '__init__.py')

        if not os.path.exists(extensions_path):
            try:
                subprocess.call(['mkdir', extensions_path])
            except OSError, e:
                _logger.error('Could not mkdir %s, %s' % (extensions_path, e))
                self._webservice_alert(_('System error.'))
                return False

        if not os.path.exists(webservice_path):
            try:
                subprocess.call(['mkdir', webservice_path])
            except OSError, e:
                _logger.error('Could not mkdir %s, %s' % (webservice_path, e))
                self._webservice_alert(_('System error.'))
                return False
            try:
                subprocess.call(['cp', init_path, webservice_path])
            except OSError, e:
                _logger.error('Could not cp %s to %s, %s' %
                              (init_path, webservice_path, e))
                self._webservice_alert(_('System error.'))
                return False

        install = False
        if not os.path.exists(os.path.join(webservice_path, 'sugarservices')):
            _logger.error('SugarServices webservice not found. Installing...')
            install = True
        elif utils.get_sugarservices_version() < \
             _REQUIRED_SUGARSERVICES_VERSION:
            _logger.error('Found old SugarServices version. Installing...')
            install = True

        if install:
            try:
                subprocess.call(['cp', '-r', sugarservices_path,
                                 webservice_path])
            except OSError, e:
                _logger.error('Could not copy %s to %s, %s' %
                              (sugarservices_path, webservice_path, e))
                self._webservice_alert(_('System error.'))
                return False

            alert = ConfirmationAlert()
            alert.props.title = _('Restart required')
            alert.props.msg = _('We needed to install some software on your '
                                'system.\nSugar must be restarted before '
                                'sugarservices can commence.')

            alert.connect('response', self._reboot_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=_('Sugar restart required.'))

        return not install

    def _webservice_alert(self, message):
        alert = ConfirmationAlert()
        alert.props.title = message
        alert.props.msg = _('We are unable to install some software on your '
                            'system.\nSugar must be upgraded before this '
                            'activity can be run.')

        alert.connect('response', self._close_alert_cb)
        self.add_alert(alert)
        self._load_intro_graphics(message=message)

    def _remove_alert_cb(self, alert, response_id):
        self.remove_alert(alert)

    def _close_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            self.close()

    def _reboot_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            try:
                utils.reboot()
            except Exception, e:
                _logger.error('Cannot reboot: %s' % e)

    def _mount_added_cb(self, volume_monitor, device):
        _logger.error('mount added')
        if self.check_volume_data():
            _logger.debug('launching')
            self._launcher()

    def _mount_removed_cb(self, volume_monitor, device):
        _logger.error('mount removed')
        if self.check_volume_data():
            _logger.debug('launching')
            self._launcher()
