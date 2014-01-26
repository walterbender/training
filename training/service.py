# Copyright (C) 2014 Walter Bender <walter@sugarlabs.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""D-bus service providing access to the shell's functionality"""

import dbus
import logging

from gi.repository import Gtk

from jarabe.model import shell
from jarabe.model import bundleregistry
from jarabe.journal import journalactivity
# from jarabe.model import network

_DBUS_SERVICE = 'org.sugarlabs.Shell'
_DBUS_SHELL_IFACE = 'org.sugarlabs.Shell'
_DBUS_PATH = '/org/sugarlabs/Shell'


class ShellService(dbus.service.Object):
    """Provides d-bus service to script the shell's operations
    Fork of sugar/src/jarabe/view/service.py
    """

    def __init__(self):
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(_DBUS_SERVICE, bus=bus)
        dbus.service.Object.__init__(self, bus_name, _DBUS_PATH)

        self._shell_model = shell.get_model()

        self._journal = journalactivity.get_journal()

        '''
        # From sugar/extensions/devices/network.py
        self._bus = dbus.SystemBus()
        self._devices = {}
        self._netmgr = None

        try:
            obj = self._bus.get_object(network.NM_SERVICE, network.NM_PATH)
            self._netmgr = dbus.Interface(obj, network.NM_IFACE)
        except dbus.DBusException:
            logging.error('%s service not available', network.NM_SERVICE)
            return

        self._netmgr.GetDevices(reply_handler=self.__get_devices_reply_cb,
                                error_handler=self.__get_devices_error_cb)

        self._bus.add_signal_receiver(self.__device_added_cb,
                                      signal_name='DeviceAdded',
                                      dbus_interface=network.NM_IFACE)
        self._bus.add_signal_receiver(self.__device_removed_cb,
                                      signal_name='DeviceRemoved',
                                      dbus_interface=network.NM_IFACE)

    def __get_devices_reply_cb(self, devices):
        for device_op in devices:
            self._check_device(device_op)

    def __get_devices_error_cb(self, err):
        logging.error('Failed to get devices: %s', err)

    def _check_device(self, device_op):
        if device_op in self._devices:
            return

        nm_device = self._bus.get_object(network.NM_SERVICE, device_op)
        props = dbus.Interface(nm_device, dbus.PROPERTIES_IFACE)

        device_type = props.Get(network.NM_DEVICE_IFACE, 'DeviceType')

        if device_type == network.NM_DEVICE_TYPE_WIFI:
            self._devices[device_op] = nm_device

            self._device_props = dbus.Interface(self._device,
                                            dbus.PROPERTIES_IFACE)
            self._device_props.GetAll(
                network.NM_DEVICE_IFACE, byte_arrays=True,
                reply_handler=self.__get_device_props_reply_cb,
                error_handler=self.__get_device_props_error_cb)

            self._device_props.Get(
                network.NM_WIRELESS_IFACE, 'ActiveAccessPoint',
                reply_handler=self.__get_active_ap_reply_cb,
                error_handler=self.__get_active_ap_error_cb)

            self._bus.add_signal_receiver(
                self.__state_changed_cb,
                signal_name='StateChanged',
                path=self._device.object_path,
                dbus_interface=network.NM_DEVICE_IFACE)

    def __device_added_cb(self, device_op):
        self._check_device(device_op)

    def __device_removed_cb(self, device_op):
        if device_op in self._devices:
            self._devices[device_op] = None
        '''

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='i', out_signature='')
    def SetZoomLevel(self, zoom_level):
        """Set Zoom Level of Sugar Shell
        """
        if zoom_level in [shell.ShellModel.ZOOM_HOME,
                          shell.ShellModel.ZOOM_MESH,
                          shell.ShellModel.ZOOM_ACTIVITY]:
            self._shell_model.set_zoom_level(zoom_level)
        return

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='i')
    def GetZoomLevel(self):
        """Get Zoom Level of Sugar Shell
        """
        return self._shell_model._get_zoom_level()

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='b')
    def IsJournal(self):
        """Is the current activity the Journal?
        """
        active_activity = self._shell_model.get_active_activity()
        return active_activity.is_journal()

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='s')
    def GetActivityName(self):
        """Get bundle name of the current activity
        """
        active_activity = self._shell_model.get_active_activity()
        return active_activity.get_activity_name()

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='b')
    def OpenJournal(self):
        """Open the journal
        """
        starting_activity = activity = self._shell_model.get_active_activity()
        while not activity.is_journal():
            activity = self._shell_model.get_next_activity(current=activity)
            if activity == starting_activity:
                return False
            if activity.is_journal():
                break
        journalactivity.get_journal().show_journal()
        activity.set_active(True)
        return True
