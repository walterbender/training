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
import email.utils
import re
from gettext import gettext as _

from gi.repository import GObject

import logging
_logger = logging.getLogger('training-activity-tasks')

from graphics import Graphics
from testutils import (get_nick, get_favorites, get_rtf, get_uitree_root,
                       get_activity, find_string, goto_home_view,
                       get_number_of_launches, is_expanded, is_fullscreen,
                       get_description)


FONT_SIZES = ['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large',
              'xx-large']

SECTIONS = [{'name': _('Welcome to One Academy'),
             'icon': 'badge-intro'},
            {'name': _('Getting to Know the Toolbar'),
             'icon': 'badge-intro'},
            {'name': _('Getting to Know the XO'),
             'icon': 'badge-intro'},
            {'name': _('Getting to Know the XO (Part 2)'),
             'icon': 'badge-intro'},
            {'name': _('More sections listed here'),
             'icon': 'badge-intro'}]


def get_task_list(task_master):
    return [[Intro1Task(task_master),
             EnterNameTask(task_master),
             EnterEmailTask(task_master),
             ValidateEmailTask(task_master),
             BadgeOneTask(task_master)],
            [Toolbars1Task(task_master),
             Toolbars2Task(task_master),
             Toolbars3Task(task_master),
             Toolbars4Task(task_master),
             Toolbars5Task(task_master),
             Toolbars6Task(task_master),
             Toolbars7Task(task_master),
             Toolbars8Task(task_master),
             BadgeTwoTask(task_master)],
            [NickChange1Task(task_master),
             NickChange2Task(task_master),
             NickChange3Task(task_master),
             NickChange4Task(task_master),
             NickChange5Task(task_master),
             WriteSave1Task(task_master),
             WriteSave2Task(task_master),
             WriteSave3Task(task_master),
             WriteSave4Task(task_master),
             WriteSave5Task(task_master),
             BadgeThreeTask(task_master)],
            [Speak1Task(task_master),
             Speak2Task(task_master),
             Speak3Task(task_master),
             Speak4Task(task_master),
             BadgeFourTask(task_master)],
            # [AddFavoriteTask(task_master),
            #  RemoveFavoriteTask(task_master),
            #  BadgeFiveTask(task_master)],
            [FinishedAllTasks(task_master)]]


class Task():
    ''' Generate class for defining tasks '''

    def __init__(self, task_master):
        self._name = 'Generic Task'
        self.uid = None
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0
        self._pause_between_tests = 1000
        self._requires = []
        self._page_count = 1

    def set_font_size(self, size):
        if size < len(FONT_SIZES):
            self._font_size = size

    def get_font_size(self):
        return self._font_size

    font_size = GObject.property(type=object, setter=set_font_size,
                                 getter=get_font_size)

    def set_zoom_level(self, level):
        self._zoom_level = level

    def get_zoom_level(self):
        return self._zoom_level

    zoom_level = GObject.property(type=object, setter=set_zoom_level,
                                  getter=get_zoom_level)

    def test(self, task_data):
        ''' The test to determine if task is completed '''
        raise NotImplementedError

    def after_button_press(self):
        ''' Anything special to do after the task is completed? '''
        return

    def get_success(self):
        ''' String to present to the user when task is completed '''
        return _('Success!')

    def get_retry(self):
        ''' String to present to the user when task is not completed '''
        return _('Keep trying')

    def get_data(self):
        ''' Any data needed for the test '''
        return None

    def skip_if_completed(self):
        ''' Should we skip this task if it is already complete? '''
        return False

    def get_pause_time(self):
        ''' How long should we pause between testing? '''
        return self._pause_between_tests

    def set_requires(self, requires):
        self._requires = requires[:]

    def get_requires(self):
        ''' Return list of tasks (uids) required prior to completing this
            task '''
        return []

    requires = GObject.property(type=object, setter=set_requires,
                                getter=get_requires)

    def is_collectable(self):
        ''' Should this task's data be collected? '''
        return False

    def get_name(self):
        ''' String to present to the user to define the task '''
        return self._name

    def get_help_info(self):
        ''' Is there help associated with this task? '''
        return (None, None)  # title, url (from Help.activity)

    def get_page_count(self):
        return self._page_count

    def get_graphics(self, page=0):
        ''' Graphics to present with the task '''
        return None

    def is_completed(self):
        ''' Has this task been marked as complete? '''
        data = self._task_master.read_task_data(self.uid)
        if data is not None and 'completed' in data:
            return data['completed']
        return False


class Intro1Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Intro One')
        self.uid = 'intro-task-1'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'introduction1.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_("Let's go!"),
                                     self._task_master.task_button_cb)
        return graphics, button


class EnterNameTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Enter Name')
        self.uid = 'enter-name-task'
        self._entries = []

    def is_collectable(self):
        return True

    def test(self, task_data):
        if len(self._entries) == 0:
            _logger.error('missing entry')
            return False
        if len(self._entries[0].get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._task_master.write_task_data('name', self._entries[0].get_text())

    def get_graphics(self, page=0):
        self._entries = []
        target = self._task_master.read_task_data('name')
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'introduction2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        if target is not None:
            self._entries.append(graphics.add_entry(text=target))
        else:
            self._entries.append(graphics.add_entry())
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class EnterEmailTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Enter Email')
        self.uid = 'enter-email-task'
        self._entries = []

    def get_requires(self):
        return ['enter-name-task']

    def test(self, task_data):
        if len(self._entries) == 0:
            _logger.error('missing entry')
            return False
        entry = self._entries[0].get_text()
        if len(entry) == 0:
            return False
        realname, email_address = email.utils.parseaddr(entry)
        if email_address == '':
            return False
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
            return False
        return True

    def after_button_press(self):
        _logger.debug('Writing email address: %s' %
                      self._entries[0].get_text())
        self._task_master.write_task_data('email_address',
                                          self._entries[0].get_text())

    def get_graphics(self, page=0):
        self._entries = []
        name = self._task_master.read_task_data('name')
        if name is not None:
            name = name.split()[0]
        else:  # Should never happen
            _logger.error('missing name')
            name = ''
        email = self._task_master.read_task_data('email_address')
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'introduction3.html?NAME=%s' % name)

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        if email is not None:
            self._entries.append(graphics.add_entry(text=email))
        else:
            self._entries.append(graphics.add_entry())
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class ValidateEmailTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Validate Email')
        self.uid = 'validate-email-task'
        self._entries = []

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['enter-email-task']

    def test(self, task_data):
        if len(self._entries) < 2:
            _logger.error('missing entry')
            return False
        entry0 = self._entries[0].get_text()
        entry1 = self._entries[1].get_text()
        if len(entry0) == 0 or len(entry1) == 0:
            return False
        if entry0 != entry1:
            return False
        realname, email_address = email.utils.parseaddr(entry0)
        if email_address == '':
            return False
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
            return False
        return True

    def after_button_press(self):
        self._task_master.write_task_data('email_address',
                                          self._entries[1].get_text())

    def get_graphics(self, page=0):
        self._entries = []
        email = self._task_master.read_task_data('email_address')
        graphics = Graphics()
        if email is not None:
            self._entries.append(graphics.add_entry(text=email))
        else:  # Should never happen
            _logger.error('missing email address')
            self._entries.append(graphics.add_entry())
        graphics.add_text('\n\n')
        graphics.add_text(
            _('Please confirm that you typed your\n'
              'email address correctly by typing it again below.\n\n'),
            size=FONT_SIZES[self._font_size])
        self._entries.append(graphics.add_entry())
        graphics.add_text('\n\n')
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeOneTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Badge One')
        self.uid = 'badge-one'

    def after_button_press(self):
        target = self._task_master.read_task_data('name').split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your first badge!" % target),
            icon='badge-intro')

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        name = self._task_master.read_task_data('name')
        if name is not None:
            target = name.split()[0]
        else:
            target = ''
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'introduction4.html?NAME=%s' % target)

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars1Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Toolbars Stop')
        self.uid = 'toolbars-task-1'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = \
                get_number_of_launches(self._task_master.activity)
            self._task_master.write_task_data(self._name, task_data)
            return False
        else:
            _logger.debug(get_number_of_launches(self._task_master.activity))
            return get_number_of_launches(self._task_master.activity) > \
                task_data['data']

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars1.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Show View Toolbar')
        self.uid = 'toolbars-task-2'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return is_expanded(self._task_master.activity.view_toolbar_button)

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars3Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Hide View Toolbar')
        self.uid = 'toolbars-task-3'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['toolbars-task-2']

    def test(self, task_data):
        return not is_expanded(self._task_master.activity.view_toolbar_button)

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars3.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars4Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Enter Fullscreen')
        self.uid = 'toolbars-task-4'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return is_fullscreen(self._task_master.activity)

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars4.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars5Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Exit Fullscreen')
        self.uid = 'toolbars-task-5'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['toolbars-task-4']

    def test(self, task_data):
        return not is_fullscreen(self._task_master.activity)

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars5.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars6Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Activity Toolbar')
        self.uid = 'toolbars-task-6'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return is_expanded(self._task_master.activity.activity_button)

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars6.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars7Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Description Box')
        self.uid = 'toolbars-task-7'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return len(get_description(self._task_master.activity)) > 0

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars7.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Toolbars8Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Description Summary')
        self.uid = 'toolbars-task-8'

    def get_requires(self):
        return ['toolbars-task-7']

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'toolbars8.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeTwoTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Badge Two')
        self.uid = 'badge-two'

    def after_button_press(self):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your second badge!" % target),
            icon='badge-intro')

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        graphics = Graphics()
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your second badge!\n\n" % target),
            bold=True,
            size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple '
              'tasks.\n'
              'Press Next to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange1Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Nick Change Step One')
        self.uid = 'nick-change-task-1'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'nickchange1.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Nick Change Step Two')
        self.uid = 'nick-change-task-2'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        graphics = Graphics()
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'nickchange2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange3Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Nick Change Step Three')
        self.uid = 'nick-change-task-3'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        graphics = Graphics()
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'nickchange3.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange4Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Nick Change Step Four')
        self.uid = 'nick-change-task-4'

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            _logger.debug('saving nick value as %s' % get_nick())
            self._task_master.write_task_data('nick', get_nick())
            task_data['data'] = get_nick()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            if not get_nick() == task_data['data']:
                task_data['new_nick'] = get_nick()
                self._task_master.write_task_data(self.uid, task_data)
                return True
            else:
                return False

    def get_graphics(self, page=0):

        def button_callback(widget):
            goto_home_view()

        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'nickchange4.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=300)
        graphics.set_zoom_level(self._zoom_level)
        graphics.add_button(_('My turn'), button_callback)
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange5Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Nick Change Step Five')
        self.uid = 'nick-change-task-5'

    def get_requires(self):
        return ['nick-change-task-4']

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self, page=0):
        nick_task_data = self._task_master.read_task_data(
            self.get_requires()[0])
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'nickchange5.html?NAME=%s' %
                           nick_task_data['new_nick'])

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave1Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Write Save Step One')
        self.uid = 'write-save-task-1'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'writesave1.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Write Save Step Two')
        self.uid = 'write-save-task-2'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'writesave2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave3Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Write Save Step Three')
        self.uid = 'write-save-task-3'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'writesave3.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave4Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Write Save Step Four')
        self.uid = 'write-save-task-4'

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        paths = get_rtf()
        for path in paths:
            # Check to see if there is a picture in the file
            if find_string(path, '\\pict'):
                return True
        return False

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self, page=0):

        def button_callback(widget):
            goto_home_view()

        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'writesave4.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=300)
        graphics.set_zoom_level(self._zoom_level)
        graphics.add_button(_('My turn'), button_callback)
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave5Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Write Save Step Five')
        self.uid = 'write-save-task-5'

    def get_requires(self):
        return ['write-save-task-4']

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'writesave5.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeThreeTask(Task):
    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Badge Three')
        self.uid = 'badge-3'

    def after_button_press(self):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your third badge!" % target),
            icon='badge-intro')

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        graphics = Graphics()
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your third badge!\n\n" % target),
            bold=True, size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple '
              'tasks.\n'
              'Press Next to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Speak1Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Speak Step One')
        self.uid = 'speak-task-1'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'speak1.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Speak2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Speak Step Two')
        self.uid = 'speak-task-2'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        graphics = Graphics()
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'speak2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Speak3Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Speak Step Three')
        self.uid = 'speak-task-3'

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        graphics = Graphics()
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'speak3.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Speak4Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Speak Step Four')
        self.uid = 'speak-task-4'

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        return len(get_activity('vu.lux.olpc.Speak')) > 0

    def get_graphics(self, page=0):

        def button_callback(widget):
            goto_home_view()

        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'speak4.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=300)
        graphics.set_zoom_level(self._zoom_level)
        graphics.add_button(_('My turn'), button_callback)
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeFourTask(Task):
    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Badge Four')
        self.uid = 'badge-4'

    def after_button_press(self):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your fourth badge!" % target),
            icon='badge-intro')

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        graphics = Graphics()
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your fourth badge!\n\n" % target),
            bold=True, size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple '
              'tasks.\n'
              'Press Next to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class AddFavoriteTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Add Favorite Task')
        self.uid = 'add-favorites-task'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            favorites_list = get_favorites()
            task_data['data'] = len(favorites_list)
            self._task_master.write_task_data(self._name, task_data)
            return False
        else:
            return len(get_favorites()) > task_data['data']

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self, page=0):
        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Help.activity', 'images',
                            'Journal_main_annotated.png')
        graphics = Graphics()
        graphics.add_text(_('Try adding a favorite to your homeview.\n\n'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class RemoveFavoriteTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Remove Favorite Task')
        self.uid = 'remove-favorites-task'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            favorites_list = get_favorites()
            task_data['data'] = len(favorites_list)
            self._task_master.write_task_data(self._name, task_data)
            return False
        else:
            return len(get_favorites()) < task_data['data']

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self, page=0):
        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Help.activity', 'images',
                            'Journal_main_annotated.png')
        graphics = Graphics()
        graphics.add_text(
            _('Now try removing a favorite to your homeview.\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeFiveTask(Task):
    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Badge Five')
        self.uid = 'badge-5'

    def after_button_press(self):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your fourth badge!" % target),
            icon='badge-intro')

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        name = self._task_master.read_task_data('name')
        if name is None:
            target = ' '
        else:
            target = name.split()[0]
        graphics = Graphics()
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your fifth badge!\n\n" % target),
            bold=True, size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple '
              'tasks.\n'
              'Press Next to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class FinishedAllTasks(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Finished All Tasks')
        self.uid = 'finished'

    def test(self, task_data):
        self._task_master.completed = True
        return True

    def get_graphics(self, page=0):
        graphics = Graphics()
        graphics.add_text(_('You are a Sugar Zenmaster.\n\n'),
                          size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class UITest(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('UI Test Task')
        self.uid = 'uitest'

    def test(self, task_data):
        return self._uitester()

    def _uitester(self):
        _logger.debug('uitree')
        uitree_root = get_uitree_root()
        _logger.debug(uitree_root)
        for node in uitree_root.get_children():
            _logger.debug('%s (%s)' % (node.name, node.role_name))
            for node1 in node.get_children():
                _logger.debug('> %s (%s)' % (node1.name, node1.role_name))
                for node2 in node1.get_children():
                    _logger.debug('> > %s (%s)' %
                                  (node2.name, node2.role_name))
        return True
