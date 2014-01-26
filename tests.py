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

import os
import json
import subprocess
import dbus

from gi.repository import Gio
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GConf
from gi.repository import GObject

from sugar3.test import uitree
from sugar3 import env
from sugar3.datastore import datastore
from sugar3 import profile
from sugar3.graphics.objectchooser import FILTER_TYPE_ACTIVITY
from sugar3.graphics.xocolor import XoColor

from jarabe.model import shell

import logging
_logger = logging.getLogger('training-activity-testutils')

_STATUS_CHARGING = 0
_STATUS_DISCHARGING = 1
_STATUS_FULLY_CHARGED = 2
_STATUS_NOT_PRESENT = 3

_UP_DEVICE_IFACE = 'org.freedesktop.UPower.Device'

_UP_TYPE_BATTERY = 2

_UP_STATE_UNKNOWN = 0
_UP_STATE_CHARGING = 1
_UP_STATE_DISCHARGING = 2
_UP_STATE_EMPTY = 3
_UP_STATE_FULL = 4
_UP_STATE_CHARGE_PENDING = 5
_UP_STATE_DISCHARGE_PENDING = 6

_WARN_MIN_PERCENTAGE = 15

volume_monitor = None
battery_model = None
proxy = None


def is_full(volume):
    # FIX ME: is volume full?
    return False


def is_writeable(path):
    # FIX ME: is path writable?
    return True


def is_landscape():
    return Gdk.Screen.width() > Gdk.Screen.height()


def get_safe_text(text):
    return GLib.markup_escape_text(text)


def get_battery_level():
    global battery_model
    if battery_model is None:
        bus = dbus.Bus(dbus.Bus.TYPE_SYSTEM)
        up_proxy = bus.get_object('org.freedesktop.UPower',
                                  '/org/freedesktop/UPower')
        upower = dbus.Interface(up_proxy, 'org.freedesktop.UPower')

        for device_path in upower.EnumerateDevices():
            device = bus.get_object('org.freedesktop.UPower', device_path)
            device_prop_iface = dbus.Interface(device, dbus.PROPERTIES_IFACE)
            device_type = device_prop_iface.Get(_UP_DEVICE_IFACE, 'Type')
            if device_type == _UP_TYPE_BATTERY:
                battery_model = DeviceModel(device)

    return battery_model.props.level


def get_sound_level():
    client = GConf.Client.get_default()
    return client.get_int('/desktop/sugar/sound/volume')


def get_volume_names():
    global volume_monitor
    if volume_monitor is None:
        volume_monitor = Gio.VolumeMonitor.get()

    names = []
    for mount in volume_monitor.get_mounts():
        names.append(mount.get_name())

    return names


def is_clipboard_text_available():
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    text_view = Gtk.TextView()
    text_buffer = text_view.get_buffer()
    text_buffer.paste_clipboard(clipboard, None, True)
    bounds = text_buffer.get_bounds()

    return len(text_buffer.get_text(bounds[0], bounds[1], True)) > 0


def get_volume_paths():
    global volume_monitor
    if volume_monitor is None:
        volume_monitor = Gio.VolumeMonitor.get()

    paths = []
    for mount in volume_monitor.get_mounts():
        paths.append(mount.get_root().get_path())

    return paths


def get_number_of_mounted_volumes():
    global volume_monitor
    if volume_monitor is None:
        volume_monitor = Gio.VolumeMonitor.get()

    return len(volume_monitor.get_mounts())


def _get_dmi(node):
    ''' The desktop management interface should be a reliable source
    for product and version information. '''
    path = os.path.join('/sys/class/dmi/id', node)
    try:
        return open(path).readline().strip()
    except:
        return None


def is_XO():
    version = _get_dmi('product_version')
    if version is None:
        hwinfo_path = '/bin/olpc-hwinfo'
        if os.path.exists(hwinfo_path) and os.access(hwinfo_path, os.X_OK):
            model = subprocess.check_output([hwinfo_path, 'model'])
            version = model.strip()
    if version in ['1', '1.5', '1.75', '4']:
        return True
    else:
        # Some systems (e.g. ARM) don't have dmi info
        if os.path.exists('/sys/devices/platform/lis3lv02d/position'):
            return True
        elif os.path.exists('/etc/olpc-release'):
            return True
    return False


def is_game_key(keyname):
    if keyname in ['KP_Up', 'KP_Down', 'KP_Left', 'KP_Right',
                   'KP_Page_Down', 'KP_Page_Up', 'KP_End', 'KP_Home']:
        return True
    else:
        return False


def is_tablet_mode():
    if not os.path.exists('/dev/input/event4'):
        return False
    try:
        output = subprocess.call(
            ['evtest', '--query', '/dev/input/event4', 'EV_SW',
             'SW_TABLET_MODE'])
    except (OSError, subprocess.CalledProcessError):
        return False
    if str(output) == '10':
        return True
    return False


def is_expanded(toolbar_button):
    return toolbar_button.is_expanded()


def is_fullscreen(activity):
    return activity._is_fullscreen


def get_starred():
    dsobjects, nobjects = datastore.find({'keep': '1'})
    return dsobjects


def get_starred_count():
    dsobjects, nobjects = datastore.find({'keep': '1'})
    return nobjects


def get_description(activity):
    if 'description' in activity.metadata:
        return activity.metadata['description']
    else:
        return ''


def get_title(activity):
    if 'title' in activity.metadata:
        return activity.metadata['title']
    else:
        return ''


def is_activity_open(bundle_name):
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        return \
            dbus.Interface(proxy, 'org.sugarlabs.Shell').GetActivityName() == \
            bundle_name and is_activity_view()
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)
        return False


def is_journal_open():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        return dbus.Interface(proxy, 'org.sugarlabs.Shell').IsJournal() and \
            is_activity_view()
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)
        return False


def is_activity_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        zoom_level = \
            dbus.Interface(proxy, 'org.sugarlabs.Shell').GetZoomLevel()
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)
        return False

    return zoom_level == shell.ShellModel.ZOOM_ACTIVITY


def is_home_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        zoom_level = \
            dbus.Interface(proxy, 'org.sugarlabs.Shell').GetZoomLevel()
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)
        return False

    return zoom_level == shell.ShellModel.ZOOM_HOME


def is_neighborhood_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        zoom_level = \
            dbus.Interface(proxy, 'org.sugarlabs.Shell').GetZoomLevel()
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)
        return False

    return zoom_level == shell.ShellModel.ZOOM_MESH


def goto_activity_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        dbus.Interface(proxy, 'org.sugarlabs.Shell').SetZoomLevel(
            shell.ShellModel.ZOOM_ACTIVITY)
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)


def goto_journal():
    ''' Actually go to the journal '''
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')
    try:
        if dbus.Interface(proxy, 'org.sugarlabs.Shell').OpenJournal():
            dbus.Interface(proxy, 'org.sugarlabs.Shell').SetZoomLevel(
                shell.ShellModel.ZOOM_ACTIVITY)
        else:
            _logger.error('Could not find journal to open???')
    except Exception, e:
        _logger.error('ERROR calling open journal: %s' % e)


def set_journal_active():
    ''' Just set the Journal as the active activity in the Home View '''
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')
    try:
        if dbus.Interface(proxy, 'org.sugarlabs.Shell').OpenJournal():
            dbus.Interface(proxy, 'org.sugarlabs.Shell').SetZoomLevel(
                shell.ShellModel.ZOOM_HOME)
        else:
            _logger.error('Could not find journal to open???')
    except Exception, e:
        _logger.error('ERROR calling open journal: %s' % e)


def goto_home_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        dbus.Interface(proxy, 'org.sugarlabs.Shell').SetZoomLevel(
            shell.ShellModel.ZOOM_HOME)
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)


def goto_neighborhood_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.sugarlabs.Shell', '/org/sugarlabs/Shell')

    try:
        dbus.Interface(proxy, 'org.sugarlabs.Shell').SetZoomLevel(
            shell.ShellModel.ZOOM_MESH)
    except Exception, e:
        _logger.error('ERROR setting zoom level %s' % e)


def get_share_scope(activity):
    if 'share-scope' in activity.metadata:
        return activity.metadata['share-scope'] == 'public'
    return False


def saw_new_launch(bundle_id, timestamp):
    for activity in get_activity(bundle_id):
        _logger.debug('%d > %d?' %
                      (get_last_launch_time(activity), int(timestamp)))
        if get_last_launch_time(activity) > int(timestamp):
            return True
    return False


def saw_new_instance(bundle_id, timestamp):
    for activity in get_activity(bundle_id):
        _logger.debug('%d > %d?' %
                      (get_creation_time(activity), int(timestamp)))
        if get_creation_time(activity) > int(timestamp):
            return True
    return False


def get_creation_time(activity):
    if 'creation_time' in activity.metadata:
        return int(activity.metadata['creation_time'])
    else:
        _logger.error('No creation time found')
        return 0


def get_last_launch_time(activity):
    if 'launch-times' in activity.metadata:
        launch_times = activity.metadata['launch-times'].split(',')
        try:
            return int(launch_times[-1])
        except Exception, e:
            _logger.error('Malformed launch times found: %s' % e)
            return 0
    else:
        # _logger.error('No launch times found')
        return 0


def get_launch_count(activity):
    if 'launch-times' in activity.metadata:
        return len(activity.metadata['launch-times'].split(','))
    else:
        return 0


def get_colors():
    client = GConf.Client.get_default()
    return XoColor(client.get_string('/desktop/sugar/user/color'))


def get_nick():
    return profile.get_nick_name()


def get_favorites():
    favorites_path = env.get_profile_path('favorite_activities')
    if os.path.exists(favorites_path):
        favorites_data = json.load(open(favorites_path))
        favorites_list = favorites_data['favorites']
    return favorites_list


def get_activity(bundle_id):
    dsobjects, nobjects = datastore.find({'activity': [bundle_id]})
    return dsobjects


def get_most_recent_instance(bundle_id):
    dsobjects, nobjects = datastore.find({'activity': [bundle_id]})
    most_recent_time = -1
    most_recent_instance = None
    for activity in dsobjects:
        last_launch_time = get_last_launch_time(activity)
        if last_launch_time > most_recent_time:
            most_recent_time = get_last_launch_time(activity)
            most_recent_instance = activity
    return most_recent_instance


def get_audio():
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['audio/ogg']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_image():
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['image/png',
                                                        'image/jpeg']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_jpg():
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['image/jpeg']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_rtf():
    dsobjects, nobjects = datastore.find({'mime_type': ['text/rtf',
                                                        'application/rtf']})
    paths = []
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_pdf():
    dsobjects, nobjects = datastore.find({'mime_type': ['application/pdf']})
    paths = []
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_odt():
    dsobjects, nobjects = datastore.find({'mime_type':
        ['application/vnd.oasis.opendocument.text']})
    paths = []
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_speak_settings(activity):
    file_path = activity.file_path
    configuration = json.loads(file(file_path, 'r').read())
    status = json.loads(configuration['status'])
    _logger.debug(status)
    return status


def get_uitree_node(name):
    return True
    uiroot = uitree.get_root()
    # print uiroot.dump()
    for node in uiroot.get_children():
        if name in [node.name, node.role_name]:
            return True
        for node1 in node.get_children():
            if name in [node1.name, node1.role_name]:
                return True
            for node2 in node1.get_children():
                if name in [node2.name, node2.role_name]:
                    return True
                for node3 in node2.get_children():
                    if name in [node3.name, node3.role_name]:
                        return True
                    for node4 in node3.get_children():
                        if name in [node4.name, node4.role_name]:
                            return True
                        for node5 in node4.get_children():
                            if name in [node5.name, node5.role_name]:
                                return True
                            for node6 in node5.get_children():
                                if name in [node6.name, node6.role_name]:
                                    # help(node6)
                                    return True
                                for node7 in node6.get_children():
                                    if name in [node7.name, node7.role_name]:
                                        return True
        return False


def find_string(path, string):
    try:
        fd = open(path, 'r')
    except Exception as e:
        _logger.error('Could not open file at %s: %s' % (path, e))
        return False
    for line in fd:
        if string in line:
            return True
    return False


class DeviceModel(GObject.GObject):
    __gproperties__ = {
        'level': (int, None, None, 0, 100, 0, GObject.PARAM_READABLE),
        'time-remaining': (int, None, None, 0, GLib.MAXINT32, 0,
                           GObject.PARAM_READABLE),  # unit: seconds
        'charging': (bool, None, None, False, GObject.PARAM_READABLE),
        'discharging': (bool, None, None, False, GObject.PARAM_READABLE),
        'present': (bool, None, None, False, GObject.PARAM_READABLE),
    }

    __gsignals__ = {
        'updated': (GObject.SignalFlags.RUN_FIRST, None, ([])),
    }

    def __init__(self, battery):
        GObject.GObject.__init__(self)
        self._battery = battery
        self._battery_props_iface = dbus.Interface(self._battery,
                                                   dbus.PROPERTIES_IFACE)
        self._battery.connect_to_signal('Changed',
                                        self.__battery_properties_changed_cb,
                                        dbus_interface=_UP_DEVICE_IFACE)
        self._fetch_properties_from_upower()

    def _fetch_properties_from_upower(self):
        """Get current values from UPower."""
        # pylint: disable=W0201
        try:
            dbus_props = self._battery_props_iface.GetAll(_UP_DEVICE_IFACE)
        except dbus.DBusException:
            logging.error('Cannot access battery properties')
            dbus_props = {}

        self._level = dbus_props.get('Percentage', 0)
        self._state = dbus_props.get('State', _UP_STATE_UNKNOWN)
        self._present = dbus_props.get('IsPresent', False)
        self._time_to_empty = dbus_props.get('TimeToEmpty', 0)
        self._time_to_full = dbus_props.get('TimeToFull', 0)

    def do_get_property(self, pspec):
        """Return current value of given GObject property."""
        if pspec.name == 'level':
            return self._level
        if pspec.name == 'charging':
            return self._state == _UP_STATE_CHARGING
        if pspec.name == 'discharging':
            return self._state == _UP_STATE_DISCHARGING
        if pspec.name == 'present':
            return self._present
        if pspec.name == 'time-remaining':
            if self._state == _UP_STATE_CHARGING:
                return self._time_to_full
            if self._state == _UP_STATE_DISCHARGING:
                return self._time_to_empty
            return 0

    def get_type(self):
        return 'battery'

    def __battery_properties_changed_cb(self):
        old_level = self._level
        old_state = self._state
        old_present = self._present
        old_time = self.props.time_remaining
        self._fetch_properties_from_upower()
        if self._level != old_level:
            self.notify('level')
        if self._state != old_state:
            self.notify('charging')
            self.notify('discharging')
        if self._present != old_present:
            self.notify('present')
        if self.props.time_remaining != old_time:
            self.notify('time-remaining')

        self.emit('updated')
