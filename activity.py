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
from shutil import copy
import json
import subprocess
from gettext import gettext as _

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
    from jarabe.view.viewhelp import ViewHelp
    _HELP_AVAILABLE = True
except:
    _HELP_AVAILABLE = False

from toolbar_utils import separator_factory, label_factory, button_factory
from taskmaster import TaskMaster
from graphics import Graphics, FONT_SIZES
from checkprogress import CheckProgress
import tests

import logging
_logger = logging.getLogger('training-activity')

_TRAINING_DATA_UID = 'training_data_uid'
_TRAINING_DATA_EMAIL = 'training_data_email'
_TRAINING_DATA_FULLNAME = 'training_data_fullname'

_MINIMUM_SPACE = 1024 * 1024 * 10  # 10MB is very conservative


class TrainingActivity(activity.Activity):
    ''' A series of training exercises '''

    def __init__(self, handle):
        ''' Initialize the toolbars and the game board '''
        try:
            super(TrainingActivity, self).__init__(handle)
        except dbus.exceptions.DBusException, e:
            _logger.error(str(e))

        self.connect('realize', self.__realize_cb)

        if hasattr(self, 'metadata') and 'font_size' in self.metadata:
            self.font_size = int(self.metadata['font_size'])
        else:
            self.font_size = 5
        self.zoom_level = self.font_size / float(len(FONT_SIZES))

        self._setup_toolbars()
        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self.bundle_path = activity.get_bundle_path()
        self._copy_entry = None
        self._paste_entry = None
        self._webkit = None
        self._clipboard_text = ''

        self.volume_data = []

        # Lots of corner cases to consider:
        # (1) We require a USB key
        # (2) Only one data file on USB key
        # (3) At least 10MB of free space
        # (4) File is read/write
        # (5) Only one set of training data per USB key
        # (6) We are resuming the activity:
        #     * Is there a data file to sync on the USB key?
        #       - Do the email addresses match?
        #     * Is there a mismatch between the instance and the USB key?
        # (7) We are launching a new instance
        #     * Is there a data file to sync on the USB key?
        #     * Create a new data file on the USB key

        # Before we begin, we need to find any and all USB keys
        # and any and all training-data files on them.
        _logger.debug(tests.get_volume_paths())
        for path in tests.get_volume_paths():
            os.path.basename(path)
            self.volume_data.append(
                {'basename': os.path.basename(path),
                 'files': tests.look_for_training_data(path),
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
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)

        # (2) Only one USB key
        if len(self.volume_data) > 1:
            _logger.error('MULTIPLE USB KEYS INSERTED')
            alert = ConfirmationAlert()
            alert.props.title = _('Multiple USB keys found')
            alert.props.msg = _('Only one USB key must be inserted while '
                                'running this program.\nPlease remove any '
                                'additional USB keys before launching '
                                'this activity.')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)

        volume = self.volume_data[0]

        # (3) At least 10MB of free space
        if tests.is_full(volume['usb_path'],
                           required=_MINIMUM_SPACE):
            _logger.error('USB IS FULL')
            alert = ConfirmationAlert()
            alert.props.title = _('USB key is full')
            alert.props.msg = _('No room on USB')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)

        # (4) File is read/write
        if not tests.is_writeable(volume['usb_path']):
            _logger.error('CANNOT WRITE TO USB')
            alert = ConfirmationAlert()
            alert.props.title = _('Cannot write to USB')
            alert.props.msg = _('USB key seems to be read-only.')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)

        # (5) Only one set of training data per USB key
        # We expect UIDs to formated as XXXX-XXXX
        # We need to make sure we have proper UIDs associated with
        # the USBs and the files on them match the UID.
        # (a) If there are no files, we will assign the UID based on the
        #     volume path;
        # (b) If there is one file with a valid UID, we use that UID;
        if len(volume['files']) == 0:
            volume['uid'] = 'training-data-%s' % \
                            tests.format_volume_name(volume['basename'])
            _logger.debug('No training data found. Using UID %s' % 
                          volume['uid'])
        elif len(volume['files']) == 1:
            volume['uid'] = 'training-data-%s' % volume['files'][0][-9:]
            _logger.debug('Training data found. Using UID %s' % 
                          volume['uid'])
        else:
            _logger.error('MULTIPLE TRAINING-DATA FILES FOUND')
            alert = ConfirmationAlert()
            alert.props.title = _('Multiple training-data files found.')
            alert.props.msg = _('There can only be one set of training '
                                'data per USB key.')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)

        # (6) We are resuming the activity
        # (7) or are we are launching a new instance.

        # We need to sync up file on USB with file on disk,
        # but only if the email addresses match. Otherwise,
        # raise an error.
        error = not self._sync_data_from_USB()
        if not error:
            self._copy_data_from_USB()
            # Flash a welcome screen
            self._load_intro_graphics(file_name='Welcome/welcome-back.html')
            GObject.timeout_add(1500, self._launch_task_master)
        else:
            # Could be a mismatch between the USB UID and the
            # instance UID, in which case, we should go with
            # the data on the USB.
            usb_path = self._check_for_USB_data()
            if usb_path is not None:
                # Start this new instance with data from the USB
                self._copy_data_from_USB()
                self._load_intro_graphics(
                    file_name='Welcome/welcome-back.html')
                GObject.timeout_add(1500, self._launch_task_master)
            else:
                self._launch_task_master()

    def _check_for_USB_data(self):
        usb_path = os.path.join(self.volume_data[0]['usb_path'],
                                self.volume_data[0]['uid'])
        if os.path.exists(usb_path):
            return usb_path
        else:
            return None

    def _sync_data_from_USB(self):
        usb_data_path = self._check_for_USB_data()
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
            if 'email_address' in usb_data:
                usb_email = usb_data['email_address']
            else:
                usb_email = None
            if 'email_address' in sugar_data:
                sugar_email = sugar_data['email_address']
            else:
                sugar_email = None
            if usb_email != sugar_email:
                if usb_email is None and sugar_email is not None:
                    _logger.warning('Using email address from Sugar: %s' %
                                    sugar_email)
                    usb_data['email_address'] = sugar_email
                elif usb_email is not None and sugar_email is None:
                    _logger.warning('Using email address from USB: %s' %
                                    usb_email)
                    sugar_data['email_address'] = usb_email
                elif usb_email is None and sugar_email is None:
                    _logger.warning('No email address found')
                else:
                    # FIX ME: We need to resolve this, but for right now, punt.
                    alert = ConfirmationAlert()
                    alert.props.title = _('Data mismatch')
                    alert.props.msg = _('Are you %s or %s?' %
                                        (usb_email, sugar_email))
                    alert.connect('response', self._remove_alert_cb)
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
                   (not 'completed' in data_one[key] or \
                   not data_one[key]['completed']):
                    data_two[key] = data_one[key]

            # Copy incompleted tasks from two to one
            for key in data_two:
                if isinstance(data_two[key], dict) and \
                   (not 'completed' in data_one[key] or \
                   not data_one[key]['completed']):
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
        else:
            _logger.error('No data to sync on USB')
        return True

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

    def _launch_task_master(self):
        self.check_progress = None

        self._load_extension()

        self._task_master = TaskMaster(self)

        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        center_in_panel.add(self._task_master)
        self._task_master.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

        Gdk.Screen.get_default().connect('size-changed', self._configure_cb)

        self._task_master.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self._task_master.connect('key_press_event',
                                  self._task_master.keypress_cb)
        self._task_master.set_can_focus(True)
        self._task_master.grab_focus()

        self.completed = False
        self._task_master.task_master()

    def _load_intro_graphics(self, file_name='generic-problem.html',
                             message=None):
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        url = os.path.join(self.bundle_path, 'html-content', file_name)
        graphics = Graphics()
        if message is None:
            graphics.add_uri('file://' + url)
        else:
            graphics.add_uri('file://' + url + '?MSG=' + \
                             tests.get_safe_text(message))
        graphics.set_zoom_level(0.667)
        center_in_panel.add(graphics)
        graphics.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

    def _configure_cb(self, event):
        self._task_master.reload_graphics()

    def write_file(self, file_path):
        if len(self.volume_data) == 1:
            self.metadata[_TRAINING_DATA_UID] = self.volume_data[0]['uid']

            # We may have failed before getting to init of taskmaster
            if hasattr(self, '_task_master'):
                self._task_master.write_task_data(
                    'current_task', self._task_master.current_task)
                self.update_activity_title()
                email = self._task_master.read_task_data('email_address')
                if email is None:
                    email = ''
                self.metadata[_TRAINING_DATA_EMAIL] = email
                name = self._task_master.read_task_data('name')
                if name is None:
                    name = ''
                self.metadata[_TRAINING_DATA_FULLNAME] = name

        self.metadata['font_size'] = str(self.font_size)

    def update_activity_title(self):
        name = self._task_master.read_task_data('name')
        if name is not None:
            bundle_name = activity.get_bundle_name()
            if self.metadata['title'] != _('%s %s Activity') % (name,
                                                                bundle_name):
                self.metadata['title'] = _('%s %s Activity') % (name,
                                                                bundle_name)

    def _setup_toolbars(self):
        ''' Setup the toolbars. '''
        self.max_participants = 1  # No sharing

        toolbox = ToolbarBox()

        self.activity_button = ActivityToolbarButton(self)
        toolbox.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        self.set_toolbar_box(toolbox)
        toolbox.show()
        self.toolbar = toolbox.toolbar

        view_toolbar = Gtk.Toolbar()
        self.view_toolbar_button = ToolbarButton(
            page=view_toolbar,
            label=_('View'),
            icon_name='toolbar-view')
        toolbox.toolbar.insert(self.view_toolbar_button, 1)
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
        toolbox.toolbar.insert(self.edit_toolbar_button, 1)
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

        self.help_button = button_factory('toolbar-help',
                                          toolbox.toolbar,
                                          self._help_cb, tooltip=_('help'),
                                          accelerator=_('<Ctrl>H'))
        self.help_button.set_sensitive(False)
        if not _HELP_AVAILABLE:
            self.help_button.hide()

        button_factory('check-progress',
                       toolbox.toolbar,
                       self._check_progress_cb,
                       tooltip=_('Check progress'))

        self.back = button_factory('go-previous-paired',
                                   toolbox.toolbar,
                                   self._go_back_cb,
                                   tooltip=_('Previous section'))
        self.back.props.sensitive = False
        self.back.hide()

        self.forward = button_factory('go-next-paired',
                                      toolbox.toolbar,
                                      self._go_forward_cb,
                                      tooltip=_('Next section'))
        self.forward.props.sensitive = False
        self.forward.hide()

        self.progress_label = label_factory(toolbox.toolbar, '', width=300)
        self.progress_label.set_use_markup(True)

        separator_factory(toolbox.toolbar, True, False)
        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

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

        self._copy_button.set_sensitive(
            webkit is not None or text_entry is not None)

    def _copy_cb(self, button):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
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

    def _check_progress_cb(self, button):
        self.check_progress = CheckProgress(self._task_master)
        self._task_master.load_progress_summary(self.check_progress)

    def _go_back_cb(self, button):
        section, task = self._task_master.get_section_index()
        if section > 0:
            section -= 1
        _logger.debug('go back %d:%d' % (section, task))
        uid = self._task_master.section_and_task_to_uid(section)
        _logger.debug('new uid %s' % (uid))
        self._task_master.current_task = \
            self._task_master.uid_to_task_number(uid)
        self._task_master.task_master()

    def _go_forward_cb(self, button):
        section, task = self._task_master.get_section_index()
        if section < self._task_master.get_number_of_sections() - 1:
            section += 1
        _logger.debug('go forward %d:%d' % (section, task))
        uid = self._task_master.section_and_task_to_uid(section)
        _logger.debug('new uid %s' % (uid))
        self._task_master.current_task = \
            self._task_master.uid_to_task_number(uid)
        self._task_master.task_master()

    def _help_cb(self, button):
        title, help_file = self._task_master.get_help_info()
        _logger.debug('%s: %s' % (title, help_file))
        if not hasattr(self, 'window_xid'):
            self.window_xid = self.get_window().get_xid()
        if title is not None and help_file is not None:
            self.viewhelp = ViewHelp(title, help_file, self.window_xid)
            self.viewhelp.show()

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

        icon_dir = os.path.join(self.bundle_path, 'icons')
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
        extensions_path = os.path.join(os.path.expanduser('~'), '.sugar',
                                      'default', 'extensions')
        webservice_path = os.path.join(extensions_path, 'webservice')
        training_path = os.path.join(self.bundle_path, 'training')
        init_path = os.path.join(self.bundle_path, 'training', '__init__.py')

        if not os.path.exists(extensions_path):
            try:
                subprocess.call(['mkdir', extensions_path])
            except OSError, e:
                _logger.error('Could not mkdir %s, %s' % (extensions_path, e))
        if not os.path.exists(webservice_path):
            try:
                subprocess.call(['mkdir', webservice_path])
            except OSError, e:
                _logger.error('Could not mkdir %s, %s' % (webservice_path, e))
            try:
                subprocess.call(['cp', init_path, webservice_path])
            except OSError, e:
                _logger.error('Could not cp %s to %s, %s' %
                              (init_path, webservice_path, e))
        if not os.path.exists(os.path.join(webservice_path, 'training')):
            _logger.error('Training webservice not found. Installing...')
            try:
                subprocess.call(['cp', '-r', training_path, webservice_path])
            except OSError, e:
                _logger.error('Could not copy %s to %s, %s' %
                              (training_path), webservice_path, e)

            alert = ConfirmationAlert()
            alert.props.title = _('Restart required')
            alert.props.msg = _('We needed to install some software on your '
                                'system.\nSugar must be restarted before '
                                'training can commence.')

            alert.connect('response', self._remove_alert_cb)
            self.add_alert(alert)

    def _remove_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            self.close()

    def _close_alert_cb(self, alert, response_id, path, old_name, new_name):
        self.remove_alert(alert)
        self.close()
