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
         'tasks': [Welcome1Task(task_master),
                   Welcome2Task(task_master),
                   Welcome3Task(task_master),
                   Welcome4Task(task_master),
                   Welcome5Task(task_master),
                   Welcome6Task(task_master),
                   Welcome7Task(task_master)]},
        {'name': _('1. Getting to Know the Toolbar'),
         'icon': 'badge-intro',
         'tasks': [Toolbar1Task(task_master),
                   Toolbar2Task(task_master),
                   Toolbar3Task(task_master),
                   Toolbar4Task(task_master),
                   Toolbar5Task(task_master),
                   Toolbar6Task(task_master),
                   Toolbar7Task(task_master),
                   Toolbar8Task(task_master),
                   Toolbar9Task(task_master)]},
        {'name': _('2. Getting Connected'),
         'icon': 'badge-intro',
         'tasks': [Connected1Task(task_master),
                   Connected2Task(task_master),
                   Connected3Task(task_master),
                   Connected4Task(task_master),
                   Connected5Task(task_master),
                   Connected6Task(task_master),
                   Connected7Task(task_master),
                   Connected8Task(task_master)]},
        {'name': _('3. Getting to Know Sugar Activities'),
         'icon': 'badge-intro',
         'tasks': [Activities1Task(task_master),
                   Activities2Task(task_master),
                   Activities3Task(task_master),
                   Activities4Task(task_master),
                   Activities5Task(task_master),
                   Activities6Task(task_master),
                   Activities7Task(task_master),
                   Activities8Task(task_master)]},
        {'name': _('4. Getting to Know the Journal'),
         'icon': 'badge-intro',
         'tasks': [Journal1Task(task_master),
                   Journal2Task(task_master),
                   Journal3Task(task_master),
                   Journal4Task(task_master),
                   Journal5Task(task_master),
                   Journal6Task(task_master),
                   Journal7Task(task_master),
                   Journal8Task(task_master)]},
        {'name': _('5. Getting to Know the Frame'),
         'icon': 'badge-intro',
         'tasks': [Frame1Task(task_master),
                   Frame2Task(task_master),
                   Frame3Task(task_master),
                   Frame4Task(task_master),
                   Frame5Task(task_master),
                   Frame6Task(task_master),
                   Frame7Task(task_master),
                   Frame8Task(task_master)]},
        {'name': _('6. Getting to Know the Views'),
         'icon': 'badge-intro',
         'tasks': [Views1Task(task_master),
                   Views2Task(task_master),
                   Views3Task(task_master),
                   Views4Task(task_master),
                   Views5Task(task_master),
                   Views6Task(task_master),
                   Views7Task(task_master),
                   Views8Task(task_master),
                   Views9Task(task_master)]},
        {'name': _('7. Getting to Know Settings'),
         'icon': 'badge-intro',
         'tasks': [Settings1Task(task_master),
                   Settings2Task(task_master),
                   Settings3Task(task_master),
                   Settings4Task(task_master),
                   Settings5Task(task_master),
                   Settings6Task(task_master)]},
        {'name': _('8. Getting to Know more Activities'),
         'icon': 'badge-intro',
         'tasks': [MoreActivities1Task(task_master),
                   Turtle1Task(task_master),
                   Physics1Task(task_master),
                   BadgeMoreActivitiesTask(task_master)]},
        {'name': _('9. Getting to Know Collaboration'),
         'icon': 'badge-intro',
         'tasks': [Physics2Task(task_master),
                   BadgeCollaborationTask(task_master)]}
    ]

    if tests.is_XO():
        task_list.append(
            {'name': _('10. Learning More About the XO'),
             'icon': 'badge-intro',
             'tasks': [XO1Task(task_master),
                       XO2Task(task_master),
                       XO3Task(task_master),
                       XO4Task(task_master),
                       XO5Task(task_master),
                       XO6Task(task_master),
                       XO7Task(task_master),
                       XO8Task(task_master)]},
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
        self._prompt = _('Next')

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
        self._task_master.activity.set_copy_widget()
        self._task_master.activity.set_paste_widget()
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
        self._height = 610

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class HTMLHomeTask(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._uri = 'Welcome/welcome1.html'
        self._height = 305

    def get_my_turn(self):
        return True

    def get_graphics(self, page=0):

        def button_callback(button):
            tests.goto_home_view()

        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        graphics.add_button(None, button_callback, button_icon='home')
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class BadgeTask(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Badge Task')
        self.uid = 'badge-task'
        self._section_index = 0
        self._title = _("Congratulations!\nYou’ve earned another badge!")
        self._uri = 'Welcome/welcome7.html'

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


class Welcome1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Welcome One')
        self.uid = 'welcome-1-task'
        self._uri = 'Welcome/welcome1.html'
        self._prompt = _("Let's go!")


class Welcome2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Enter Your Name')  # Welcome Two
        self.uid = 'enter-name-task'  # 'welcome-2-task'
        self._uri = 'Welcome/welcome2.html'
        self._entry = None
        self._height = 400

    def is_collectable(self):
        return True

    def test(self, task_data):
        if self._entry is None:
            _logger.error('missing entry')
            return False
        if len(self._entry.get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._task_master.write_task_data('name', self._entry.get_text())
        self._task_master.activity.update_activity_title()

    def get_graphics(self, page=0):
        self._entry = None
        target = self._get_user_name()
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        if target is not None:
            self._entry = graphics.add_entry(text=target)
        else:
            self._entry = graphics.add_entry()

        self._task_master.activity.set_copy_widget(text_entry=self._entry)
        self._task_master.activity.set_paste_widget(text_entry=self._entry)

        return graphics, self._prompt


class Welcome3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Welcome Three')
        self.uid = 'welcome-3-task'
        self._uri = 'Welcome/welcome3.html'

    def get_graphics(self, page=0):
        name = self._get_user_name().split()[0]
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s' %
                           (self._uri, tests.get_safe_text(name)))
        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Welcome4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter Your Email')  # Welcome Four
        self.uid = 'enter-email-task'  # 'welcome-4-task'
        self._uri = 'Welcome/welcome4.html'
        self._entry = None
        self._height = 400

    def get_requires(self):
        return ['enter-name-task']

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        if self._entry is None:
            _logger.error('missing entry')
            return False
        entry = self._entry.get_text()
        if len(entry) == 0:
            return False
        realname, email_address = email.utils.parseaddr(entry)
        if email_address == '':
            return False
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
            return False
        return True

    def after_button_press(self):
        _logger.debug('Writing email address: %s' % self._entry.get_text())
        self._task_master.write_task_data('email_address',
                                          self._entry.get_text())

    def get_graphics(self, page=0):
        self._entry = []
        email = self._task_master.read_task_data('email_address')
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        if email is not None:
            self._entry = graphics.add_entry(text=email)
        else:
            self._entry = graphics.add_entry()

        self._task_master.activity.set_copy_widget(text_entry=self._entry)
        self._task_master.activity.set_paste_widget(text_entry=self._entry)

        return graphics, self._prompt


class Welcome5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Validate Email')  # Welcome Five
        self.uid = 'validate-email-task' # 'welcome-5-task'
        self._uri = 'Welcome/welcome5.html'
        self._entries = []

    def is_collectable(self):
        return True

    def skip_if_completed(self):
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
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        self._entries.append(graphics.add_entry(text=email))
        webkit = graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)
        if email is None:  # Should never happen
            email = ''
        self._entries.append(graphics.add_entry())
        # Paste to second entry
        self._task_master.activity.set_copy_widget(text_entry=self._entries[0])
        self._task_master.activity.set_paste_widget(
            text_entry=self._entries[-1])

        return graphics, self._prompt


class Welcome6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Welcome Four')
        self.uid = 'welcome-6-task'
        self._uri = 'Welcome/welcome6.html'


class Welcome7Task(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Welcome Seven')
        self.uid = 'welcome-7-task'
        self._uri = 'Welcome/welcome7.html'
        self._title = _("Congratulations!\nYou’ve earned your first badge!")
        self._section_index = 0

    def get_graphics(self, page=0):
        name = self._get_user_name().split()[0]
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s' %
                           (self._uri, tests.get_safe_text(name)))
        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Toolbar1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Introduction to the Toolbar')
        self.uid = 'toolbar-1-task'
        self._uri = 'Toolbar/toolbar1.html'


class Toolbar2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Stopping an Activity')
        self.uid = 'toolbar-2-task'
        self._uri = 'Toolbar/toolbar2.html'


class Toolbar3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Stopping an Activity Video')
        self.uid = 'toolbar-3-task'
        self._uri = 'Toolbar/toolbar3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task']

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
            launch_count = tests.get_launch_count(self._task_master.activity)
            if launch_count > task_data['data']:
                return True
            else:
                # FIX ME: If the user switches to a new instance, the
                # the launch count is no longer valid. Reseting it here,
                # but this may require an extra cycle of stop and start.
                task_data['data'] = launch_count


class Toolbar4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('More re Toolbars')
        self.uid = 'toolbar-4-task'
        self._uri = 'Toolbar/toolbar4.html'


class Toolbar5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Using the View Menu')
        self.uid = 'toolbar-5-task'
        self._uri = 'Toolbar/toolbar5.html'


class Toolbar6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Trying Full Screen')
        self.uid = 'toolbar-6-task'
        self._uri = 'Toolbar/toolbar6.html'
        self._goals = []

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        if len(self._goals) == 0:
            if tests.is_expanded(
                    self._task_master.activity.view_toolbar_button):
                self._goals.append(True)
        elif len(self._goals) == 1:
            if tests.is_fullscreen(self._task_master.activity):
                self._goals.append(True)
        elif len(self._goals) == 2:
            if not tests.is_fullscreen(self._task_master.activity):
                self._goals.append(True)
        else:
            return not tests.is_expanded(
                self._task_master.activity.view_toolbar_button)

class Toolbar7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Activity Toolbar')
        self.uid = 'toolbar-7-task'
        self._uri = 'Toolbar/toolbar7.html'


class Toolbar8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter a Description')
        self.uid = 'toolbar-8-task'
        self._uri = 'Toolbar/toolbar8.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        return len(tests.get_description(self._task_master.activity)) > 0


class Toolbar9Task(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Toolbar Badge')
        self.uid = 'toolbar-9-task'
        self._uri = 'Toolbar/toolbar9.html'
        self._section = 1


class Connected1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting Connected')
        self.uid = 'connected-1-task'
        self._uri = 'Connected/connected1.html'


class Connected2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Network View')
        self.uid = 'connected-2-task'
        self._uri = 'Connected/connected2.html'


class Connected3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Connecting to a WiFi Network')
        self.uid = 'connected-3-task'
        self._uri = 'Connected/connected3.html'


class Connected4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Connecting to a WiFi Network Video')
        self.uid = 'connected-4-task'
        self._uri = 'Connected/connected4.html'

    def get_refresh(self):
        return True

    def test(self, task_data):
        return tests.nm_status() == 'network-wireless-connected'

    def is_collectable(self):
        return True


class Connected5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _("You're online")
        self.uid = 'connected-5-task'
        self._uri = 'Connected/connected5.html'
        self._entries = []

    def skip_if_completed(self):
        return True

    def get_requires(self):
        return ['enter-name-task', 'enter-email-task']

    def test(self, task_data):
        if len(self._entries) < 2:
            _logger.error('missing entry')
            return False
        entry0 = self._entries[0].get_text()
        entry1 = self._entries[1].get_text()
        if len(entry0) == 0 or len(entry1) == 0:
            return False
        realname, email_address = email.utils.parseaddr(entry1)
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
        name = self._task_master.read_task_data('name')
        if name is None:  # Should never happen
            name = ''
        email = self._task_master.read_task_data('email_address')
        if email is None:  # Should never happen
            email = ''
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s&EMAIL=%s' %
                           (self._uri,
                            tests.get_safe_text(name),
                            tests.get_safe_text(email)))

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)
        self._entries.append(graphics.add_entry(text=name))
        self._entries.append(graphics.add_entry(text=email))
        # Copy/Paste to second entry
        self._task_master.activity.set_copy_widget(text_entry=self._entries[1])
        self._task_master.activity.set_paste_widget(
            text_entry=self._entries[1])

        return graphics, self._prompt


class Connected6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter School Name')  # Connected Six
        self.uid = 'enter-school-name-task'  # 'connected-6-task'
        self._entry = None
        self._height = 400
        self._uri = 'Connected/connected6.html'

    def is_collectable(self):
        return True

    def test(self, task_data):
        if self._entry is None:
            _logger.error('missing entry')
            return False
        if len(self._entry.get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._task_master.write_task_data('school_name',
                                          self._entry.get_text())

    def get_graphics(self, page=0):
        self._entries = []
        target = self._task_master.read_task_data('school_name')
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        if target is not None:
            self._entry = graphics.add_entry(text=target)
        else:
            self._entry = graphics.add_entry()

        self._task_master.activity.set_copy_widget(text_entry=self._entry)
        self._task_master.activity.set_paste_widget(text_entry=self._entry)

        return graphics, self._prompt


class Connected7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Connected')
        self.uid = 'connected-7-task'
        self._uri = 'Connected/connected7.html'

    def get_requires(self):
        return ['enter-name-task', 'enter-email-task',
                'enter-school-name-task']

    def get_graphics(self, page=0):
        self._entries = []
        name = self._task_master.read_task_data('name')
        if name is None:  # Should never happen
            name = ''
        email = self._task_master.read_task_data('email_address')
        if email is None:  # Should never happen
            email = ''
        school = self._task_master.read_task_data('school_name')
        if school is None:  # Should never happen
            school = ''
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s&EMAIL=%s&SCHOOL=%s' %
                           (self._uri,
                            tests.get_safe_text(name),
                            tests.get_safe_text(email),
                            tests.get_safe_text(school)))

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Connected8Task(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Connected Badge')
        self.uid = 'connected-8-task'
        self._uri = 'Connected/connected8.html'
        self._section = 2


class Activities1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know Sugar Activities')
        self.uid = 'activities-1-task'
        self._uri = 'Activities/activities1.html'


class Activities2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Take a Picture with Record')
        self.uid = 'activities-2-task'
        self._uri = 'Activities/activities2.html'


class Activities3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Take a Picture with Record Video')
        self.uid = 'record-save-task'  # 'activities-3-task'
        self._uri = 'Activities/activities3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        if not tests.saw_new_launch('org.laptop.RecordActivity',
                                    task_data['start_time']):
            return False
        paths = tests.get_jpg()
        return len(paths) > 0


class Activities4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Insert a Picture into a Write Document')
        self.uid = 'activities-4-task'
        self._uri = 'Activities/activities4.html'


class Activities5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Insert a Picture into a Write Document Video')
        self.uid = 'write-save-task'  # 'activities-5-task'
        self._uri = 'Activities/activities5.html'

    def get_requires(self):
        return ['validate-email-task', 'record-save-task']

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def skip_if_completed(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        if not tests.saw_new_launch('org.laptop.AbiWordActivity',
                                    task_data['start_time']):
            return False
        # We need the clipboard text for the Speak task
        if not tests.is_clipboard_text_available():
            return False
        paths = tests.get_odt()
        for path in paths:
            # Check to see if there is a picture in the file:
            # look for '\\pict' in RTF, 'Pictures' in ODT
            if tests.find_string(path, 'Pictures'):
                return True
        return False


class Activities6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Make Speak Talk to You')
        self.uid = 'activities-6-task'
        self._uri = 'Activities/activities6.html'


class Activities7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Make Speak Talk to You Video')
        self.uid = 'speak-task'  # 'activities-7-task'
        self._uri = 'Activities/activities7.html'

    def get_requires(self):
        return ['validate-email-task', 'write-save-task']

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def skip_if_completed(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        if not tests.saw_new_launch('vu.lux.olpc.Speak',
                                    task_data['start_time']):
            return False
        # Has any setting changed?
        status = tests.get_speak_settings(
            tests.get_most_recent_instance('vu.lux.olpc.Speak'))
        if len(status['eyes']) != 2 or \
           status['eyes'][0] != 1 or \
           status['pitch'] != 49 or \
           status['rate'] != 49 or \
           status['mouth'] != 1:
            return True
        return False


class Activities8Task(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Activities Badge')
        self.uid = 'activities-8-task'
        self._uri = 'Activities/activities8.html'
        self._section = 3


class Journal1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know the Journal')
        self.uid = 'journal-1-task'
        self._uri = 'Journal/journal1.html'


class Journal2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Viewing the Journal')
        self.uid = 'journal-2-task'
        self._uri = 'Journal/journal2.html'


class Journal3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Viewing the Journal Video')
        self.uid = 'journal-3-task'
        self._uri = 'Journal/journal3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            activity = tests.get_most_recent_instance(
                'org.laptop.AbiWordActivity')
            if activity is not None and 'description' in activity.metadata:
                task_data['data'] = activity.metadata['description']
            else:
                task_data['data'] = ''
            return False
        else:
            # Make sure description has changed and entry is 'starred'
            activity = tests.get_most_recent_instance(
                'org.laptop.AbiWordActivity')
            if activity is None or not 'keep' in activity.metadata or \
               not 'description' in activity.metadata:
                return False
            return \
                not task_data['data'] == activity.metadata['description'] \
                and int(activity.metadata['keep']) == 1


class Journal4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Introducing the Portfolio')
        self.uid = 'journal-4-task'
        self._uri = 'Journal/journal4.html'


class Journal5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Usining the Portfolio Video')
        self.uid = 'journal-5-task'
        self._uri = 'Journal/journal5.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        # Make sure there are newly starred items and that the Portfolio
        # activity has been launched; then look for a PDF file.
        if task_data['data'] is None:
            task_data['data'] = tests.get_starred_count()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        if not tests.get_starred_count() > task_data['data']:
            return False
        if not tests.saw_new_launch('org.sugarlabs.PortfolioActivity',
                                    task_data['start_time']):
            return False
        paths = tests.get_pdf()
        # FIX ME: test file creation time
        return len(paths) > 0


class Journal6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Copy your Presentation to USB')
        self.uid = 'journal-6-task'
        self._uri = 'Journal/journal6.html'


class Journal7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Copy your Presentation to USB')
        self.uid = 'journal-7-task'
        self._uri = 'Journal/journal7.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task', 'journal-5-task']

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def skip_if_completed(self):
        return True

    def test(self, task_data):
        files = tests.look_for_file_type(
            self._task_master.activity.volume_data[0]['usb_path'], '.pdf')
        # FIX ME: test file creation time
        return len(files) > 0


class Journal8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Journal Badge')
        self.uid = 'journal-8-task'
        self._uri = 'Journal/journal8.html'
        self._section = 4


class Frame1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know the Frame')
        self.uid = 'frame-1-task'
        self._uri = 'Frame/frame1.html'


class Frame2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Three Ways to Open the Frame')
        self.uid = 'frame-2-task'
        self._uri = 'Frame/frame2.html'

    # FIX ME: We need some sort of test here


class Frame3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Checking the Battery')
        self.uid = 'frame-3-task'
        self._uri = 'Frame/frame3.html'
        self._battery_level = None
        self._height = 400

    def get_requires(self):
        return ['validate-email-task']

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

    def get_graphics(self, page=0):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        buttons = graphics.add_radio_buttons(['battery-000', 'battery-020',
                                              'battery-040', 'battery-060',
                                              'battery-080', 'battery-100'],
                                             colors=tests.get_colors())
        for i, button in enumerate(buttons):
            button.connect('clicked', self._battery_button_callback, i)
            button.set_active(False)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Frame4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Changing the Volume')
        self.uid = 'frame-4-task'
        self._uri = 'Frame/frame4.html'

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = tests.get_sound_level()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            return not tests.get_sound_level() == task_data['data']


class Frame5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Using the Frame to Read Text')
        self.uid = 'frame-5-task'
        self._uri = 'Frame/frame5.html'

    # FIX ME: We need some sort of test here


class Frame6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Bottom of the Frame Recap')
        self.uid = 'frame-6-task'
        self._uri = 'Frame/frame6.html'


class Frame7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Top of the Frame Recap')
        self.uid = 'frame-7-task'
        self._uri = 'Frame/frame7.html'


class Frame8Task(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Frame Badge')
        self.uid = 'frame-8-task'
        self._uri = 'Frame/frame8.html'
        self._section = 5


class Views1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know the Views')
        self.uid = 'views-1-task'
        self._uri = 'Views/views1.html'


class Views2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Four Views of Sugar')
        self.uid = 'views-2-task'
        self._uri = 'Views/views2.html'


class Views3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Views of Sugar Video')
        self.uid = 'views-3-task'
        self._uri = 'Views/views3.html'

    def get_refresh(self):
        return True


class Views4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Adding a Favourite to the Home View')
        self.uid = 'views-4-task'
        self._uri = 'Views/views4.html'


class Views5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Adding a Favourite to the Home View Video')
        self.uid = 'views-5-task'
        self._uri = 'Views/views5.html'

    def get_requires(self):
        return ['validate-email-task']

    def get_refresh(self):
        return True

    def is_collectable(self):
        return True

    def get_my_turn(self):
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


class Views6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Removing a Favourite from the Home View')
        self.uid = 'views-6-task'
        self._uri = 'Views/views6.html'


class Views7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Removing a Favourite from the Home View Video')
        self.uid = 'views-7-task'
        self._uri = 'Views/views7.html'

    def get_requires(self):
        return ['validate-email-task', 'views-5-task']

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def get_my_turn(self):
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


class Views8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch Between the Four Views')
        self.uid = 'views-8-task'
        self._uri = 'Views/views8.html'
        self._views = []

    def get_requires(self):
        return ['validate-email-task']

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


class Views9Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Views Badge')
        self.uid = 'views-9-task'
        self._uri = 'Views/views9.html'
        self._section = 6


class Settings1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Exploring the Sugar Settings')
        self.uid = 'settings-1-task'
        self._uri = 'Settings/settings1.html'


class Settings2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Changing the XO Nickname and Colours')
        self.uid = 'settings-2-task'
        self._uri = 'Settings/settings2.html'


class Settings3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Changing the XO Nickname and Colours Video')
        self.uid = 'settings-3-task'
        self._uri = 'Settings/settings3.html'

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def skip_if_completed(self):
        return True

    def get_my_turn(self):
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


class Settings4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Important Settings')
        self.uid = 'settings-4-task'
        self._uri = 'Settings/settings4.html'


class Settings5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Other settings')
        self.uid = 'settings-5-task'
        self._uri = 'Settings/settings5.html'


class Settings6Task(BadgeTask):
    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('Badge Settings')
        self.uid = 'settings-6-task'
        self._uri = 'Settings/settings6.html'
        self._section_index = 7


class MoreActivities1Task(HTMLTask):
    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Learning About More Activities')
        self.uid = 'more-activities-1-task'
        self._uri = 'MoreActivities/moreactivities1.html'


class Turtle1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Square')
        self.uid = 'turtle-task-1'
        self._uri = 'MoreActivities/turtle1.html'

    def get_requires(self):
        return ['validate-email-task']

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


class Physics1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Physics Play')
        self.uid = 'physics-play-task'
        self._uri = 'MoreActivities/physics1.html'

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        return tests.saw_new_launch('org.laptop.physics',
                                    task_data['start_time'])

    def get_my_turn(self):
        return True


class Physics2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Physics Share')
        self.uid = 'physics-share-task'
        self._uri = 'Collaboration/physics2.html'

    def get_requires(self):
        return ['validate-email-task']

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
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        self._entries.append(graphics.add_entry())

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget(text_entry=self._entries[-1])

        return graphics, self._prompt

    def test(self, task_data):
        if not tests.is_clipboard_text_available():
            return False
        if len(self._entries[0].get_text()) > 0:
            return True
        return False


class XO1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Learning More About the XO')
        self.uid = 'xo-1-task'
        self._uri = 'XO/xo1.html'


class XO2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch to Tablet Mode')
        self.uid = 'xo-2-task'
        self._uri = 'XO/xo2.html'


class XO3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch to Tablet Mode Video')
        self.uid = 'xo-3-task'
        self._uri = 'XO/xo3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        return tests.is_tablet_mode()


class XO4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Play with the Gamepad Keys')
        self.uid = 'xo-4-task'
        self._uri = 'XO/xo4.html'

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


class XO5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch Back to Laptop Mode')
        self.uid = 'xo-5-task'
        self._uri = 'XO/xo5.html'


class XO6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch Back to Laptop Mode Video')
        self.uid = 'xo-6-task'
        self._uri = 'XO/xo6.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return ['validate-email-task', 'xo-3-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        return not btests.is_tablet_mode()


class XO7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Change the Screen Orientation')
        self.uid = 'xo-7-task'
        self._uri = 'XO/xo7.html'
        self._goals = []

    def get_requires(self):
        return ['validate-email-task']

    def is_collectable(self):
        return True

    def test(self, task_data):
        if len(self._goals) == 0:
            if not tests.is_landscape():
                self._goals.append(True)
            return False
        elif len(self._goals) == 1:
            if tests.is_landscape():
                self._goals.append(True)
            return False
        elif len(self._goals) == 2:
            if not tests.is_landscape():
                self._goals.append(True)
            return False
        else:
            return tests.is_landscape()


class XO8Task(BadgeTask):

    def __init__(self, task_master):
        BadgeTask.__init__(self, task_master)
        self._name = _('XO Badge')
        self.uid = 'xo-8-task'
        self._uri = 'XO/xo8.html'
        self._section = 10


class Finished1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Fill out a form 1')
        self.uid = 'finished-task-1'
        self._uri = 'finished1.html'

    def get_requires(self):
        return ['validate-email-task']

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

        self._task_master.activity.set_copy_widget()
        self._task_master.activity.set_paste_widget()

        return graphics, _('Done')
