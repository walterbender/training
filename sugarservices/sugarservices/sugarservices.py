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

'''D-bus service providing access to various Sugar services.'''

import os
import dbus
import json
import logging

from jarabe import config
from jarabe.model import shell
from jarabe.model import session
from jarabe.model import network
from jarabe.journal import journalactivity
from jarabe.webservice.accountsmanager import get_webaccount_services

from sugar3 import env
from sugar3.test import uitree

_user_extensions_path = os.path.join(env.get_profile_path(), 'extensions')

_DBUS_SERVICE = 'org.sugarlabs.SugarServices'
_DBUS_SHELL_IFACE = 'org.sugarlabs.SugarServices'
_DBUS_PATH = '/org/sugarlabs/SugarServices'

_VERSION = 5


def _get_webservice_paths():
    paths = []
    for path in [os.path.join(_user_extensions_path, 'webservice'),
                 os.path.join(config.ext_path, 'webservice')]:
        if os.path.exists(path):
            paths.append(path)
    return paths


def _get_webservice_module_paths():
    webservice_module_paths = []
    for webservice_path in _get_webservice_paths():
        for path in os.listdir(webservice_path):
            service_path = os.path.join(webservice_path, path)
            if os.path.isdir(service_path):
                webservice_module_paths.append(service_path)
    return webservice_module_paths


class SugarServices(dbus.service.Object):
    '''
    Provides d-bus service to script Sugar shell operations
    Fork of sugar/src/jarabe/view/service.py

    Also provides d-bus service to the Sugar Journal to Network Manager
    Fork of sugar/extensions/devices/network.py
    '''

    def __init__(self):
        self._version = _VERSION
        self._shell_model = None
        self._session = None
        self._journal = None
        self._network = None

        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(_DBUS_SERVICE, bus=bus)
        dbus.service.Object.__init__(self, bus_name, _DBUS_PATH)

        try:
            self._shell_model = shell.get_model()
            logging.debug('SUGARSERVICES GOT SHELL MODEL')
        except Exception, e:
            logging.error('Problem getting shell model: %s' % e)

        try:
            self._session = session.get_session_manager()
            logging.debug('SUGARSERVICES GOT SESSION MANAGER')
        except Exception, e:
            logging.error('Problem getting session manager: %s' % e)

        try:
            self._network = NetworkManagerObserver()
            logging.debug('SUGARSERVICES GOT NETWORK MANAGER')
        except Exception, e:
            logging.error('Problem getting NetworkManager: %s' % e)
            return

        '''
        try:
            self._webservices = get_webaccount_services()
        except Exception, e:
            logging.error('Problem getting Webservices: %s' % e)
            return

        logging.debug('Sugar Services launched...')
        '''

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='i')
    def GetVersion(self):
        '''Get version number of SugarServices
        '''
        return self._version

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='')
    def Reboot(self):
        '''Reboot Sugar
        '''
        self._session.reboot()

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='i', out_signature='')
    def SetZoomLevel(self, zoom_level):
        '''Set Zoom Level of Sugar Shell
        '''
        if zoom_level in [shell.ShellModel.ZOOM_HOME,
                          shell.ShellModel.ZOOM_MESH,
                          shell.ShellModel.ZOOM_ACTIVITY]:
            self._shell_model.set_zoom_level(zoom_level)
        return

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='i')
    def GetZoomLevel(self):
        '''Get Zoom Level of Sugar Shell
        '''
        return self._shell_model._get_zoom_level()

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='b')
    def IsJournal(self):
        '''Is the current activity the Journal?
        '''
        active_activity = self._shell_model.get_active_activity()
        return active_activity.is_journal()

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='s')
    def GetActivityName(self):
        '''Get bundle name of the current activity
        '''
        active_activity = self._shell_model.get_active_activity()
        return active_activity.get_activity_name()

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='b')
    def OpenJournal(self):
        '''Open the journal
        '''
        starting_activity = activity = self._shell_model.get_active_activity()
        while not activity.is_journal():
            activity = self._shell_model.get_next_activity(current=activity)
            if activity == starting_activity:
                return False
            if activity.is_journal():
                break

        if self._journal is None:
            try:
                self._journal = journalactivity.get_journal()
                logging.debug('SUGARSERVICES GOT JOURNAL')
            except Exception, e:
                logging.error('Problem getting Journal: %s' % e)

        if self._journal is not None:
            self._journal.show_journal()

        activity.set_active(True)
        return True

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='s')
    def Dump(self):
        '''Dump the uitree
        '''
        logging.error('DUMP')
        uiroot = uitree.get_root()
        result = uiroot.dump()
        logging.error(results)
        return json.dumps(result)

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='s', out_signature='b')
    def FindChild(self, target):
        '''Find a child in the uitree
        '''
        uiroot = uitree.get_root()
        node = uiroot.find_child(name=target)
        return node is not None

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='s', out_signature='b')
    def Click(self, target):
        '''Find a child in the uitree and 'click'
        '''
        uiroot = uitree.get_root()
        node = uiroot.find_child(name=target)
        if node is not None:
            node.do_action('click')
            return True
        else:
            return False

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='s')
    def NMStatus(self):
        for key in self._network._devices:
            return(str(self._network._devices[key].device_view.status))

    @dbus.service.method(_DBUS_SHELL_IFACE,
                         in_signature='', out_signature='s')
    def GetWebServiceModulePaths(self):
        paths = _get_webservice_module_paths()
        return json.dumps(paths)


class NetworkManagerObserver(object):
    ''' Borrowing liberally from sugar/extensions/devices/network.py
    '''

    def __init__(self):
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

        # Could expand to other devices, but for the time being, we
        # only care about wireless devices.
        device_type = props.Get(network.NM_DEVICE_IFACE, 'DeviceType')
        if device_type == network.NM_DEVICE_TYPE_WIFI:
            device = WirelessDeviceObserver(nm_device)
            self._devices[device_op] = device

    def __device_added_cb(self, device_op):
        self._check_device(device_op)

    def __device_removed_cb(self, device_op):
        if device_op in self._devices:
            device = self._devices[device_op]
            device.disconnect()
            del self._devices[device_op]


class WirelessDeviceObserver(object):

    def __init__(self, device):
        self._device = device
        self.device_view = WirelessDevice(self._device)

    def disconnect(self):
        self.device_view.disconnect()
        del self.device_view
        self.device_view = None


class WirelessDevice():
    ''' Similar to DeviceView, but absent any UI. Just maintaining the
        state of the device.
    '''

    def __init__(self, device):
        self.status = 'init'
        self.state = ''
        self.address = None
        self._bus = dbus.SystemBus()
        self._device = device
        self._device_props = None
        self._flags = 0
        self._ssid = ''
        self._display_name = ''
        self._mode = network.NM_802_11_MODE_UNKNOWN
        self._strength = 0
        self._frequency = 0
        self._device_state = None
        self._active_ap_op = None

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

    def disconnect(self):
        self._bus.remove_signal_receiver(
            self.__state_changed_cb,
            signal_name='StateChanged',
            path=self._device.object_path,
            dbus_interface=network.NM_DEVICE_IFACE)

    def __get_device_props_reply_cb(self, properties):
        if 'State' in properties:
            self._device_state = properties['State']
            self._update_state()

    def __get_device_props_error_cb(self, err):
        logging.error('Error getting the device properties: %s', err)

    def __get_active_ap_reply_cb(self, active_ap_op):
        if self._active_ap_op != active_ap_op:
            if self._active_ap_op is not None:
                self._bus.remove_signal_receiver(
                    self.__ap_properties_changed_cb,
                    signal_name='PropertiesChanged',
                    path=self._active_ap_op,
                    dbus_interface=network.NM_ACCESSPOINT_IFACE)
            if active_ap_op == '/':
                self._active_ap_op = None
                return
            self._active_ap_op = active_ap_op
            active_ap = self._bus.get_object(network.NM_SERVICE, active_ap_op)
            props = dbus.Interface(active_ap, dbus.PROPERTIES_IFACE)

            props.GetAll(network.NM_ACCESSPOINT_IFACE, byte_arrays=True,
                         reply_handler=self.__get_all_ap_props_reply_cb,
                         error_handler=self.__get_all_ap_props_error_cb)

            self._bus.add_signal_receiver(
                self.__ap_properties_changed_cb,
                signal_name='PropertiesChanged',
                path=self._active_ap_op,
                dbus_interface=network.NM_ACCESSPOINT_IFACE,
                byte_arrays=True)

    def __get_active_ap_error_cb(self, err):
        logging.error('Error getting the active access point: %s', err)

    def __state_changed_cb(self, new_state, old_state, reason):
        self._device_state = new_state
        self._update_state()
        self._device_props.Get(network.NM_WIRELESS_IFACE, 'ActiveAccessPoint',
                               reply_handler=self.__get_active_ap_reply_cb,
                               error_handler=self.__get_active_ap_error_cb)

    def __ap_properties_changed_cb(self, properties):
        self._update_properties(properties)

    def _update_properties(self, properties):
        if 'Mode' in properties:
            self._mode = properties['Mode']
        if 'Ssid' in properties:
            self._ssid = properties['Ssid']
            self._display_name = network.ssid_to_display_name(self._ssid)
        if 'Strength' in properties:
            self._strength = properties['Strength']
        if 'Flags' in properties:
            self._flags = properties['Flags']
        if 'Frequency' in properties:
            self._frequency = properties['Frequency']

        if self._mode == network.NM_802_11_MODE_ADHOC and \
           network.is_sugar_adhoc_network(self._ssid):
            pass

        self._update()

    def __get_all_ap_props_reply_cb(self, properties):
        self._update_properties(properties)

    def __get_all_ap_props_error_cb(self, err):
        logging.error('Error getting the access point properties: %s', err)

    def _update(self):
        self._update_state()

    def _update_state(self):
        if self._active_ap_op is not None:
            self.state = self._device_state
        else:
            self.state = network.NM_DEVICE_STATE_UNKNOWN

        if self._mode != network.NM_802_11_MODE_ADHOC and \
                network.is_sugar_adhoc_network(self._ssid) is False:
            if self.state == network.NM_DEVICE_STATE_ACTIVATED:
                self.status = 'network-wireless-connected'
            else:
                self.status = 'network-wireless-disconnected'

        else:
            channel = network.frequency_to_channel(self._frequency)
            if self.state == network.NM_DEVICE_STATE_ACTIVATED:
                self.status = 'network-adhoc-%s-connected' \
                    % channel
            else:
                self.status = 'network-adhoc-%s-disconnected' % channel

        if self.state == network.NM_DEVICE_STATE_PREPARE or \
           self.state == network.NM_DEVICE_STATE_CONFIG or \
           self.state == network.NM_DEVICE_STATE_NEED_AUTH or \
           self.state == network.NM_DEVICE_STATE_IP_CONFIG or \
           self.state == network.NM_DEVICE_STATE_IP_CHECK or \
           self.state == network.NM_DEVICE_STATE_SECONDARIES:
            pass
        elif self.state == network.NM_DEVICE_STATE_ACTIVATED:
            self.address = self._device_props.Get(
                network.NM_DEVICE_IFACE, 'Ip4Address')
        else:
            self.state = 'unknown'

    def __deactivate_connection_cb(self, palette, data=None):
        network.disconnect_access_points([self._active_ap_op])

    def __activate_reply_cb(self, connection):
        logging.debug('Network created: %s', connection)

    def __activate_error_cb(self, err):
        logging.debug('Failed to create network: %s', err)
