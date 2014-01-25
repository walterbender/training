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

from sugar3.datastore import datastore

import logging
_logger = logging.getLogger('training-activity-tasks')

from graphics import Graphics, FONT_SIZES
import tests


def get_tasks(task_master):
    task_list = [
        {'name': _('Welcome to One Academy'),
         'icon': 'badge-intro',
         'tasks': [Intro1Task(task_master),
                   EnterNameTask(task_master),
                   BadgeIntroTask(task_master)]},
        {'name': _('1. Getting to Know the Toolbar'),
         'icon': 'badge-intro',
         'tasks': [Toolbars0Task(task_master),
                   Toolbars1Task(task_master),
                   Toolbars2Task(task_master),
                   Toolbars3Task(task_master),
                   Toolbars4Task(task_master),
                   Toolbars5Task(task_master),
                   Toolbars6Task(task_master),
                   Toolbars7Task(task_master),
                   Toolbars8Task(task_master),
                   BadgeToolbarTask(task_master)]},
        {'name': _('2. Getting Connected'),
         'icon': 'badge-intro',
         'tasks': [Network1Task(task_master),
                   EnterSchoolNameTask(task_master),
                   EnterEmailTask(task_master),
                   ValidateEmailTask(task_master),
                   BadgeNetworkTask(task_master)]},
        {'name': _('3. Getting to Know Sugar Activities'),
         'icon': 'badge-intro',
         'tasks': [Record1Task(task_master),
                   WriteSave1Task(task_master),
                   WriteSave2Task(task_master),
                   WriteSave3Task(task_master),
                   WriteSave4Task(task_master),
                   WriteSave5Task(task_master),
                   Speak1Task(task_master),
                   Speak2Task(task_master),
                   Speak3Task(task_master),
                   Speak4Task(task_master),
                   BadgeActivitiesTask(task_master)]},
        {'name': _('4. Getting to Know the Journal'),
         'icon': 'badge-intro',
         'tasks': [Journal1Task(task_master),
                   AddStarredTask(task_master),
                   RemoveStarredTask(task_master),
                   BadgeJournalTask(task_master)]},
        {'name': _('5. Getting to Know the Frame'),
         'icon': 'badge-intro',
         'tasks': [ClipboardTask(task_master),
                   BatteryTask(task_master),
                   SoundTask(task_master),
                   BadgeFrameTask(task_master)]},
        {'name': _('6. Getting to Know the Views'),
         'icon': 'badge-intro',
         'tasks': [Views1Task(task_master),
                   Views2Task(task_master),
                   AddFavoriteTask(task_master),
                   RemoveFavoriteTask(task_master),
                   BadgeViewsTask(task_master)]},
        {'name': _('7. Getting to Know Settings'),
         'icon': 'badge-intro',
         'tasks': [NickChange1Task(task_master),
                   NickChange2Task(task_master),
                   NickChange3Task(task_master),
                   NickChange4Task(task_master),
                   NickChange5Task(task_master),
                   BadgeSettingsTask(task_master)]},
        {'name': _('8. Getting to Know more Activities'),
         'icon': 'badge-intro',
         'tasks': [Turtle1Task(task_master),
                   Physics1Task(task_master),
                   BadgeMoreActivitiesTask(task_master)]},
        {'name': _('9. Getting to Know Collaboration'),
         'icon': 'badge-intro',
         'tasks': [Physics2Task(task_master),
                   BadgeCollaborationTask(task_master)]}
    ]

    if tests.is_XO():
        task_list.append(
            {'name': _('10. Getting to Know the XO'),
             'icon': 'badge-intro',
             'tasks': [Tablet1Task(task_master),
                       Rotate1Task(task_master),
                       Rotate2Task(task_master),
                       GameKeyTask(task_master),
                       Tablet2Task(task_master),
                       BadgeXOTask(task_master)]}
        )

    task_list.append(
        {'name': _('Wrap Up'),
         'icon': 'badge-intro',
         'tasks': [Finished1Task(task_master),
                   FinishedAllTasks(task_master)]}
    )

    return task_list


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

    def get_refresh(self):
        ''' Does the task need a refresh button for its graphics? '''
        return False

    def get_my_turn(self):
        ''' Does the task need a my turn button to goto home view? '''
        return False

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
        return None, _('Next')

    def is_completed(self):
        ''' Has this task been marked as complete? '''
        data = self._task_master.read_task_data(self.uid)
        if data is not None and 'completed' in data:
            return data['completed']
        return False

    def _get_user_name(self):
        ''' Get user's name. '''
        name = self._task_master.read_task_data('name')
        if name is not None:
            return name
        else:
            return ''


class HTMLTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._uri = 'introduction1.html'
        self._prompt = _('Next')
        self._height = 610

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        return graphics, self._prompt


class HTMLHomeTask(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._uri = 'introduction1.html'
        self._prompt = _('Next')
        self._height = 305

    def get_my_turn(self):
        return True

    def get_graphics(self, page=0):

        def button_callback(button):
            tests.goto_home_view()

        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        graphics.add_button(None, button_callback, button_icon='home')
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))

        return graphics, self._prompt


class Intro1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Intro One')
        self.uid = 'intro-task-1'
        self._uri = 'introduction1.html'
        self._prompt = _("Let's go!")


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
        self._task_master.activity.update_activity_title()

    def get_graphics(self, page=0):
        self._entries = []
        target = self._get_user_name()
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'introduction2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)
        if target is not None:
            self._entries.append(graphics.add_entry(text=target))
        else:
            self._entries.append(graphics.add_entry())

        return graphics, _('Next')


class EnterSchoolNameTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Enter School Name')
        self.uid = 'enter-school-name-task'
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
        self._task_master.write_task_data('school_name',
                                          self._entries[0].get_text())

    def get_graphics(self, page=0):
        self._entries = []
        target = self._task_master.read_task_data('school_name')
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'network2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        if target is not None:
            self._entries.append(graphics.add_entry(text=target))
        else:
            self._entries.append(graphics.add_entry())

        return graphics, _('Next')


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
        name = self._get_user_name().split()[0]
        email = self._task_master.read_task_data('email_address')
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'introduction3.html?NAME=%s' %
                           tests.get_safe_text(name))

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        if email is not None:
            self._entries.append(graphics.add_entry(text=email))
        else:
            self._entries.append(graphics.add_entry())

        return graphics, _('Next')


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

        return graphics, _('Next')


class Toolbars0Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Toolbars test')
        self.uid = 'toolbars-task-0'
        self._uri = 'toolbars0.html'

    def get_refresh(self):
        return True


class Toolbars1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Toolbars Stop')
        self.uid = 'toolbars-task-1'
        self._uri = 'toolbars1.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = \
                tests.get_launch_count(self._task_master.activity)
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            _logger.debug(tests.get_launch_count(self._task_master.activity))
            return tests.get_launch_count(self._task_master.activity) > \
                task_data['data']


class Toolbars2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Show View Toolbar')
        self.uid = 'toolbars-task-2'
        self._uri = 'toolbars2.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return tests.is_expanded(self._task_master.activity.view_toolbar_button)


class Toolbars3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Hide View Toolbar')
        self.uid = 'toolbars-task-3'
        self._uri = 'toolbars3.html'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['toolbars-task-2']

    def test(self, task_data):
        return not tests.is_expanded(
            self._task_master.activity.view_toolbar_button)


class Toolbars4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter Fullscreen')
        self.uid = 'toolbars-task-4'
        self._uri = 'toolbars4.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return tests.is_fullscreen(self._task_master.activity)


class Toolbars5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Exit Fullscreen')
        self.uid = 'toolbars-task-5'
        self._uri = 'toolbars5.html'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['toolbars-task-4']

    def test(self, task_data):
        return not tests.is_fullscreen(self._task_master.activity)


class Toolbars6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Activity Toolbar')
        self.uid = 'toolbars-task-6'
        self._uri = 'toolbars6.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return tests.is_expanded(self._task_master.activity.activity_button)


class Toolbars7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Description Box')
        self.uid = 'toolbars-task-7'
        self._uri = 'toolbars7.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return len(tests.get_description(self._task_master.activity)) > 0


class Toolbars8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Description Summary')
        self.uid = 'toolbars-task-8'
        self._uri = 'toolbars8.html'

    def get_requires(self):
        return ['toolbars-task-7']

    def test(self, task_data):
        return self._task_master.button_was_pressed


class NickChange1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Nick Change Step One')
        self.uid = 'nick-change-task-1'
        self._uri = 'nickchange1.html'


class NickChange2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Nick Change Step Two')
        self.uid = 'nick-change-task-2'
        self._uri = 'nickchange2.html'

    def test(self, task_data):
        return self._task_master.button_was_pressed


class NickChange3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Nick Change Step Three')
        self.uid = 'nick-change-task-3'
        self._uri = 'nickchange3.html'

    def get_refresh(self):
        return True


class NickChange4Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Nick Change Step Four')
        self.uid = 'nick-change-task-4'
        self._uri = 'nickchange4.html'

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            _logger.debug('saving nick value as %s' % tests.get_nick())
            self._task_master.write_task_data('nick', tests.get_nick())
            task_data['data'] = tests.get_nick()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            if not tests.get_nick() == task_data['data']:
                task_data['new_nick'] = tests.get_nick()
                self._task_master.write_task_data(self.uid, task_data)
                return True
            else:
                return False


class NickChange5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Nick Change Step Five')
        self.uid = 'nick-change-task-5'
        self._uri = 'nickchange5.html'

    def get_requires(self):
        return ['nick-change-task-4']

    def get_graphics(self, page=0):
        nick_task_data = self._task_master.read_task_data(
            self.get_requires()[0])
        if 'new_nick' in nick_task_data:
            new_nick = nick_task_data['new_nick']
        else:
            new_nick = ''
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           'nickchange5.html?NAME=%s' % new_nick)

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        return graphics, _('Next')


class Turtle1Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Turtle Square')
        self.uid = 'turtle-task-1'
        self._uri = 'turtle1.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if not tests.saw_new_launch('org.laptop.TurtleArtActivity',
                                    task_data['start_time']):
            return False
        for activity in tests.get_activity('org.laptop.TurtleArtActivity'):
            path = activity.file_path
            if not tests.find_string(path, 'left') and \
               not tests.find_string(path, 'right'):
                return False
            if not tests.find_string(path, 'forward') and \
               not tests.find_string(path, 'back'):
                return False
            return True
        return False

    def get_my_turn(self):
        return True


class Physics1Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Physics Play')
        self.uid = 'physics-play-task'
        self._uri = 'physics1.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return tests.saw_new_launch('org.laptop.physics',
                                    task_data['start_time'])

    def get_my_turn(self):
        return True


class Physics2Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Physics Share')
        self.uid = 'physics-share-task'
        self._uri = 'physics2.html'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['physics-play-task']

    def test(self, task_data):
        for activity in tests.get_activity('org.laptop.physics'):
            if tests.get_share_scope(activity):
                return True
        return False

    def get_my_turn(self):
        return True


class Record1Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Record Save')
        self.uid = 'record-save-task-1'
        self._uri = 'recordsave1.html'

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        if not tests.saw_new_launch('org.laptop.RecordActivity',
                                    task_data['start_time']):
            return False
        paths = tests.get_jpg()
        return len(paths) > 0

    def get_my_turn(self):
        return True


class WriteSave1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Write Save Step One')
        self.uid = 'write-save-task-1'
        self._uri = 'writesave1.html'


class WriteSave2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Write Save Step Two')
        self.uid = 'write-save-task-2'
        self._uri = 'writesave2.html'


class WriteSave3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Write Save Step Three')
        self.uid = 'write-save-task-3'
        self._uri = 'writesave3.html'

    def get_refresh(self):
        return True


class WriteSave4Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Write Save Step Four')
        self.uid = 'write-save-task-4'
        self._uri = 'writesave4.html'

    def get_requires(self):
        return ['record-save-task-1']

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        if not tests.saw_new_launch('org.laptop.AbiWordActivity',
                                    task_data['start_time']):
            return False
        paths = tests.get_odt()
        for path in paths:
            # Check to see if there is a picture in the file:
            # look for '\\pict' in RTF, 'Pictures' in ODT
            if tests.find_string(path, 'Pictures'):
                return True
        return False

    def get_my_turn(self):
        return True


class WriteSave5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Write Save Step Five')
        self.uid = 'write-save-task-5'
        self._uri = 'writesave5.html'

    def get_requires(self):
        return ['write-save-task-4']


class Speak1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Speak Step One')
        self.uid = 'speak-task-1'
        self._uri = 'speak1.html'


class Speak2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Speak Step Two')
        self.uid = 'speak-task-2'
        self._uri = 'speak2.html'


class Speak3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Speak Step Three')
        self.uid = 'speak-task-3'
        self._uri = 'speak3.html'


class Speak4Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Speak Step Four')
        self.uid = 'speak-task-4'
        self._uri = 'speak4.html'

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        return tests.saw_new_launch('vu.lux.olpc.Speak',
                                    task_data['start_time'])

    def get_my_turn(self):
        return True


class AddFavoriteTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Add Favorite Task')
        self.uid = 'add-favorites-task'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            favorites_list = tests.get_favorites()
            task_data['data'] = len(favorites_list)
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            return len(tests.get_favorites()) > task_data['data']

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

        return graphics, _('Next')


class RemoveFavoriteTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Remove Favorite Task')
        self.uid = 'remove-favorites-task'

    def get_requires(self):
        return ['add-favorites-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            favorites_list = tests.get_favorites()
            task_data['data'] = len(favorites_list)
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            return len(tests.get_favorites()) < task_data['data']

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

        return graphics, _('Next')


class Journal1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Introducing the Journal')
        self.uid = 'journal-task-1'
        self._uri = 'journal1.html'


class Views1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Introducing the Views')
        self.uid = 'views-task-1'
        self._uri = 'views1.html'


class Views2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Exploring the Views')
        self.uid = 'views-task-2'
        self._uri = 'views2.html'
        self._views = []

    def is_collectable(self):
        return True

    def test(self, task_data):
        if tests.is_activity_view():
            if 'activity' not in self._views:
                self._views.append('activity')
        elif tests.is_home_view():
            if 'home' not in self._views:
                self._views.append('home')
        elif tests.is_neighborhood_view():
            if 'neighborhood' not in self._views:
                self._views.append('neighborhood')
        return len(self._views) > 2


class AddStarredTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Add Starred Task')
        self.uid = 'add-starred-task'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = tests.get_starred_count()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            return tests.get_starred_count() > task_data['data']

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_my_turn(self):
        return True

    def get_graphics(self, page=0):

        def button_callback(button):
            tests.goto_journal()

        graphics = Graphics()
        graphics.add_text(
            _('Try adding a star from an item in your journal.\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_button(None, button_callback,
                            button_icon='activity-journal')
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))

        return graphics, _('Next')


class RemoveStarredTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Remove Starred Task')
        self.uid = 'remove-starred-task'

    def get_requires(self):
        return ['add-starred-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = tests.get_starred_count()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            return tests.get_starred_count() < task_data['data']

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_my_turn(self):
        return True

    def get_graphics(self, page=0):

        def button_callback(button):
            tests.goto_journal()

        graphics = Graphics()
        graphics.add_text(
            _('Now try removing a star from an item in your journal.\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_button(None, button_callback,
                            button_icon='activity-journal')
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))

        return graphics, _('Next')


class ClipboardTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Copy to Clipboard')
        self.uid = 'copy-to-clipboard-task'
        self._uri = 'clipboard1.html'
        self._entries = []
        self._prompt = _('Next')
        self._height = 500

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        self._entries.append(graphics.add_entry())
        return graphics, self._prompt

    def test(self, task_data):
        if not tests.is_clipboard_text_available():
            return False
        if len(self._entries[0].get_text()) > 0:
            return True
        return False

class BatteryTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Battery Task')
        self.uid = 'battery-task'
        self._battery_level = None

    def is_collectable(self):
        return True

    def test(self, task_data):
        if self._battery_level is None:
            return False
        level = tests.get_battery_level()
        if abs(level - self._battery_level) <= 10:
            return True
        else:
            return False

    def _battery_button_callback(self, widget, i):
        self._battery_level = i * 20

    def get_my_turn(self):
        return True

    def get_graphics(self, page=0):
        graphics = Graphics()
        graphics.add_text(_('Check the battery levels and then click\n'
                            'on the matching battery indicator.\n\n'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
        buttons = graphics.add_radio_buttons(['battery-000', 'battery-020',
                                              'battery-040', 'battery-060',
                                              'battery-080', 'battery-100'],
                                             colors=tests.get_colors())
        for i, button in enumerate(buttons):
            button.connect('clicked', self._battery_button_callback, i)
            button.set_active(False)

        return graphics, _('Next')


class SoundTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Sound Task')
        self.uid = 'sound-task'
        self._battery_level = None

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = tests.get_sound_level()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            return not tests.get_sound_level() == task_data['data']

    def get_my_turn(self):
        return True

    def get_graphics(self, page=0):
        graphics = Graphics()
        graphics.add_text(_('Check the sound level and then use\n'
                            'the slider to adjust it.\n\n'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))

        return graphics, _('Next')


class GameKeyTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Game Key Task')
        self.uid = 'game-task'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            self._task_master.grab_focus()
            self._task_master.keyname = None
            task_data['data'] = ' '
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            if tests.is_game_key(self._task_master.keyname):
                task_data['data'] = self._task_master.keyname
                self._task_master.write_task_data(self.uid, task_data)
                return True
            else:
                return False

    def get_graphics(self, page=0):

        graphics = Graphics()
        graphics.add_text(_('Click on a Game Key'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'),
                          size=FONT_SIZES[self._font_size])

        return graphics, _('Next')


class Tablet1Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Tablet Task 1')
        self.uid = 'tablet-task-1'

    def is_collectable(self):
        return True

    def test(self, task_data):
        return tests.is_tablet_mode()

    def get_graphics(self, page=0):

        graphics = Graphics()
        graphics.add_text(_('Switch to Tablet Mode'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'),
                          size=FONT_SIZES[self._font_size])
        return graphics, _('Next')


class Tablet2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Tablet Task 2')
        self.uid = 'tablet-task-2'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['tablet-task-1']

    def test(self, task_data):
        return not tests.is_tablet_mode()

    def get_graphics(self, page=0):

        graphics = Graphics()
        graphics.add_text(_('Switch to back to Laptop Mode'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'),
                          size=FONT_SIZES[self._font_size])

        return graphics, _('Next')


class Rotate1Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Rotate Task 1')
        self.uid = 'rotate-task-1'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['tablet-task-1']

    def test(self, task_data):
        return not tests.is_landscape()

    def get_graphics(self, page=0):

        graphics = Graphics()
        graphics.add_text(_('Hit the rotate button to switch to '
                            'Portrait mode.'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'),
                          size=FONT_SIZES[self._font_size])

        return graphics, _('Next')


class Rotate2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Rotate Task 2')
        self.uid = 'rotate-task-2'

    def is_collectable(self):
        return True

    def get_requires(self):
        return ['tablet-task-1']

    def test(self, task_data):
        return tests.is_landscape()

    def get_graphics(self, page=0):

        graphics = Graphics()
        graphics.add_text(_('Hit the rotate button to switch to '
                            'Landscape mode.'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'),
                          size=FONT_SIZES[self._font_size])

        return graphics, _('Next')


class Network1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Network 1')
        self.uid = 'network-task-1'
        self._uri = 'network1.html'

    def is_collectable(self):
        return True


class Finished1Task(HTMLHomeTask):

    def __init__(self, task_master):
        HTMLHomeTask.__init__(self, task_master)
        self._name = _('Fill out a form 1')
        self.uid = 'finished-task-1'
        self._uri = 'finished1.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = _('Assessment') + ' ' + self._get_user_name()
            self._task_master.write_task_data(self.uid, task_data)
            # Create the assessment document in the Journal
            dsobject = datastore.create()
            if dsobject is not None:
                _logger.debug('creating Assessment entry in Journal')
                dsobject.metadata['title'] = task_data['data'] + '.rtf'
                dsobject.metadata['icon-color'] = \
                    tests.get_colors().to_string()
                dsobject.metadata['tags'] = \
                    self._task_master.activity.volume_data[0]['uid']
                dsobject.metadata['mime_type'] = 'text/rtf'
                dsobject.set_file_path(
                    os.path.join(self._task_master.activity.bundle_path,
                                 'Assessment.rtf'))
                datastore.write(dsobject)
                dsobject.destroy()
            return False
        else:
            # Look for the assessment document on the USB stick
            # FIX ME: What if they changed the name???
            _logger.debug(os.path.join(
                self._task_master.activity.volume_data[0]['usb_path'],
                task_data['data'] + '.rtf'))
            return os.path.exists(os.path.join(
                self._task_master.activity.volume_data[0]['usb_path'],
                task_data['data'] + '.rtf'))


class BadgeTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Badge Task')
        self.uid = 'badge-task'
        self._section_index = 0
        self._title = _("Congratulations!\nYou’ve earned another badge!")
        self._message = _('Click on Next to go to your next one!')


    def after_button_press(self):
        task_data = self._task_master.read_task_data(self.uid)
        if not 'badge' in task_data:
            task_data['badge'] = True
            self._task_master.activity.add_badge(
                self._title,
                icon=self._task_master.get_section_icon(self._section_index))
            self._task_master.write_task_data(self.uid, task_data)

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        graphics = Graphics()
        graphics.add_text(self._title, bold=True,
                          size=FONT_SIZES[self._font_size])
        graphics.add_icon(
            self._task_master.get_section_icon(self._section_index))
        graphics.add_text(
            '\n\n' + self._name + '\n\n' + self._message + '\n\n',
            size=FONT_SIZES[self._font_size])

        return graphics, _('Next')


class BadgeIntroTask(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Intro')
        self.uid = 'badge-intro'
        self._section_index = 0
        self._title = _("Congratulations!\nYou’ve earned your first badge!")


class BadgeToolbarTask(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Toolbar')
        self._section_index = 1
        self.uid = 'badge-toolbar'


class BadgeNetworkTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Network')
        self._section_index = 2
        self.uid = 'badge-network'


class BadgeActivitiesTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Activities')
        self._section_index = 3
        self.uid = 'badge-activities'


class BadgeJournalTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Journal')
        self._section_index = 4
        self.uid = 'badge-journal'


class BadgeFrameTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Frame')
        self._section_index = 5
        self.uid = 'badge-frame'


class BadgeViewsTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge View')
        self._section_index = 6
        self.uid = 'badge-view'


class BadgeSettingsTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Settings')
        self._section_index = 7
        self.uid = 'badge-settings'


class BadgeMoreActivitiesTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge More Activities')
        self._section_index = 8
        self.uid = 'badge-more-activities'


class BadgeCollaborationTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Collaboration')
        self._section_index = 9
        self.uid = 'badge-collaboration'


class BadgeXOTask(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge XO')
        self._section_index = 10
        self.uid = 'badge-xo'


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

        return graphics, _('Done')
