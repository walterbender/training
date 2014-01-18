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

from sugar3.test import uitree
from sugar3 import env
from sugar3.datastore import datastore
from sugar3 import profile
from sugar3.graphics.objectchooser import FILTER_TYPE_ACTIVITY

from jarabe.model import shell

import logging
_logger = logging.getLogger('training-activity-testutils')


def is_expanded(toolbar_button):
    return toolbar_button.is_expanded()


def is_fullscreen(activity):
    return activity._is_fullscreen


def get_description(activity):
    if 'description' in activity.metadata:
        return activity.metadata['description']
    else:
        return ''


def is_activity_open(bundle_name):
    return bundle_name == shell.get_model().get_activity_name() and \
        is_activity_view()


def is_journal_open():
    return shell.get_model().is_journal() and is_activity_view()


def is_activity_view():
    return shell.get_model().props.zoom_level == \
        shell.ShellModel.ZOOM_ACTIVITY


def is_home_view():
    return shell.get_model().props.zoom_level == shell.ShellModel.ZOOM_HOME


def is_neighborhood_view():
    return shell.get_model().props.zoom_level == shell.ShellModel.ZOOM_MESH


def goto_activity_view():
    shell.get_model().set_zoom_level(shell.ShellModel.ZOOM_ACTIVITY)


def goto_home_view():
    shell.get_model().set_zoom_level(shell.ShellModel.ZOOM_HOME)


def goto_neighborhood_view():
    shell.get_model().set_zoom_level(shell.ShellModel.ZOOM_MESH)


def get_number_of_launchs(activity):
    if 'launch-times' in activity.metadata:
        return len(activity.metadata['launch-times'].split(','))
    else:
        return 0


def get_nick():
    return profile.get_nick_name()


def get_favorites():
    favorites_path = env.get_profile_path('favorite_activities')
    if os.path.exists(favorites_path):
        favorites_data = json.load(open(favorites_path))
        favorites_list = favorites_data['favorites']
    return favorites_list


def get_activity(activity):
    dsobjects, nobjects = datastore.find({'activity': [activity]})
    return dsobjects


def get_audio(self):
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['audio/ogg']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_image(self):
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['image/png',
                                                        'image/jpeg']})
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


def get_uitree_root():
    return uitree.get_root()


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
