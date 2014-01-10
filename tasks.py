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
from gettext import gettext as _

import logging
_logger = logging.getLogger('training-activity-tasks')

from sugar3 import env
from sugar3 import profile
from sugar3.graphics import style
from sugar3.test import uitree


FONT_SIZES = ['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large',
              'xx-large']


def get_favorites():
    favorites_path = env.get_profile_path('favorite_activities')
    if os.path.exists(favorites_path):
        favorites_data = json.load(open(favorites_path))
        favorites_list = favorites_data['favorites']
    return favorites_list


class Task():
    ''' Generate class for defining tasks '''

    def __init__(self, activity):
        self.name = 'Generic Task'
        self.uid = None
        self._activity = activity

    def test(self, exercises, task_data):
        ''' The test to determine if task is completed '''
        raise NotImplementedError

    def after_button_press(self):
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

    def get_pause_time(self):
        return 5000

    def get_prompt(self):
        ''' String to present to the user to define the task '''
        raise NotImplementedError

    def get_help_info(self):
        return (None, None)

    def get_graphics(self):
        ''' Graphics to present with the task '''
        return None


class IntroTask(Task):
    def __init__(self, activity):
        self.name = _('Intro Task')
        self.uid = 'introtask'
        self.entries = [None]
        self._activity = activity

    def get_prompt(self):
        pass

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        return self._activity.button_was_pressed

    def get_graphics(self):
        return self._activity.make_intro_graphic(
            '<span foreground="%s" size="%s"><b>%s</b></span>\n\n\n' %
            (style.COLOR_BLACK.get_html(),
             FONT_SIZES[5], _('Welcome to One Academy')) +
            '<span foreground="%s" size="%s">%s</span>' %
            (style.COLOR_BLACK.get_html(),
             FONT_SIZES[4], _('Are you ready to learn?')),
            'one-academy', button_label=_("Let's go!"))


class EnterNameTask(Task):

    def __init__(self, activity):
        self.name = _('Enter Name Task')
        self.uid = 'nametask'
        self.entries = []
        self._activity = activity

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) == 0:
            _logger.error('MISSING ENTRY')
            return False
        if len(self.entries[0].get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._activity.write_task_data('name', self.entries[0].get_text())

    def get_prompt(self):
        return self.name

    def get_graphics(self):
        return self._activity.make_entry_graphic(
            self, [{'title': 'name',
                    'caption':
                    _('See that progress bar at the bottom of your screen?\n\
It fills up when you complete tasks.\n\
Complete tasks to earn badges...\n\
Earn all the badges and you’ll be XO-Certified!\n\n\n\
Time for the first task:\n\
Write your full name in the box below, then press Next')}])


class EnterEmailTask(Task):

    def __init__(self, activity):
        self.name = _('Enter Email Task')
        self.uid = 'email'
        self.entries = []
        self._activity = activity

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) == 0:
            _logger.error('MISSING ENTRY')
            return False
        if len(self.entries[0].get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._activity.write_task_data('email_address',
                                       self.entries[0].get_text())

    def get_prompt(self):
        return self.name

    def get_graphics(self):
        return self._activity.make_entry_graphic(
            self, [{'title': 'email address',
                    'caption': _('Please enter your email address.')}])


class ChangeNickTask(Task):

    def __init__(self, activity):
        self.name = _('Change Nick Task')
        self.uid = 'nick1'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.error('first attempt: saving nick value as %s' %
                          profile.get_nick_name())
            self._activity.write_task_data('nick', profile.get_nick_name())
            return False
        else:
            target = self._activity.read_task_data('nick')
            _logger.error('%d attempt: comparing %s to %s' %
                          (task_data['attempt'], profile.get_nick_name(),
                           target))
            return not profile.get_nick_name() == target

    def get_prompt(self):
        return self.name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Home_fav-menu.png')
        return self._activity.make_image_graphic(
            [{'title': _('Change your nick'), 'path': file_path}])


class RestoreNickTask(Task):

    def __init__(self, activity):
        self.name = _('Restore Nick Task')
        self.uid = 'nick2'
        self._activity = activity
        self._target = self._activity.read_task_data('nick')

    def test(self, exercises, task_data):
        result = profile.get_nick_name() == self._target
        if result:
            self._activity.add_badge(
                _('Congratulations! You changed your nickname.'))
        return result

    def get_prompt(self):
        return self.name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Home_fav-menu.png')
        return self._activity.make_image_graphic(
            [{'title': _('Restore your nick to %s' % (self._target)),
              'path': file_path}])


class AddFavoriteTask(Task):

    def __init__(self, activity):
        self.name = _('Add Favorite Task')
        self.uid = 'favorites1'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.error('first attempt: saving favorites list')
            favorites_list = get_favorites()
            self._activity.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = self._activity.read_task_data('favorites')
            return favorites_count > saved_favorites_count

    def get_prompt(self):
        return self.name

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Journal_main_annotated.png')
        return self._activity.make_image_graphic(
            [{'title': _('Add a favorite'), 'path': file_path}])
        '''
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'html',
                                 'home_view.html')
        _logger.error(url)
        return make_html_graphic('file://' + url)
        '''


class RemoveFavoriteTask(Task):

    def __init__(self, activity):
        self.name = _('Remove Favorite Task')
        self.uid = 'favorites2'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            favorites_list = get_favorites()
            self._activity.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = self._activity.read_task_data('favorites')
            result = favorites_count < saved_favorites_count
            if result:
                self._activity.add_badge(
                    _('Congratulations! You changed your '
                      'favorite activities.'))
            return result

    def get_prompt(self):
        return self.name

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Journal_main_annotated.png')
        return self._activity.make_image_graphic(
            [{'title': _('Remove a favorite'), 'path': file_path}])


class FinishedAllTasks(Task):

    def __init__(self, activity):
        self.name = _('Finished All Tasks')
        self.uid = 'finished'
        self._activity = activity

    def test(self, exercises, task_data):
        self._activity.completed = True
        return True

    def get_prompt(self):
        return self.name

    def get_graphics(self):
        return self._activity.make_image_graphic(
            [{'title': _('You are a Sugar Zenmaster.')}])


class UITest(Task):

    def __init__(self, activity):
        self.name = _('UI Test Task')
        self.uid = 'uitest'
        self._activity = activity

    def test(self, exercises, task_data):
        return self._uitester()

    def _uitester(self):
        _logger.error('uitree')
        _logger.error(uitree.get_root())
        for node in uitree.get_root().get_children():
            _logger.error('%s (%s)' % (node.name, node.role_name))
            for node1 in node.get_children():
                _logger.error('> %s (%s)' % (node1.name, node1.role_name))
                for node2 in node1.get_children():
                    _logger.error('> > %s (%s)' %
                                  (node2.name, node2.role_name))
        return True
