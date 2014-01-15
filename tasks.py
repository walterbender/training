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

from gi.repository import Gtk
from gi.repository import GObject

import logging
_logger = logging.getLogger('training-activity-tasks')

from sugar3 import env
from sugar3 import profile
from sugar3.graphics import style
from sugar3.test import uitree

from graphics import Graphics


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
        self._name = 'Generic Task'
        self.uid = None
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

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

    def requires(self):
        ''' Return list of tasks (uids) required prior to completing this
            task '''
        return []

    def is_collectable(self):
        ''' Should this task's data be collected? '''
        return True

    def get_name(self):
        ''' String to present to the user to define the task '''
        raise NotImplementedError

    def get_help_info(self):
        return (None, None)

    def get_graphics(self):
        ''' Graphics to present with the task '''
        return None

    def is_completed(self):
        data = self._activity.read_task_data(self.uid)
        if data is not None and 'completed' in data:
            return data['completed']
        return False


class IntroTask(Task):
    def __init__(self, activity):
        self._name = _('Intro Task')
        self.uid = 'intro-task'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        return self._activity.button_was_pressed

    def get_graphics(self):
        graphics = Graphics()
        '''
        graphics.add_text(_('Welcome to One Academy\n\n'),
                          bold=True,
                          size=FONT_SIZES[self._font_size],
                          justify=Gtk.Justification.CENTER)
        graphics.add_icon('one-academy', stroke=style.COLOR_BLACK.get_svg())
        graphics.add_text(_('\nAre you ready to learn?\n\n'),
                          justify=Gtk.Justification.CENTER,
                          size=FONT_SIZES[self._font_size])
        '''
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'introduction1.html')
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_("Let's go!"),
                                     self._activity.task_button_cb)
        return graphics, button


class EnterNameTask(Task):

    def __init__(self, activity):
        self._name = _('Enter Name Task')
        self.uid = 'enter-name-task'
        self.entries = []
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) == 0:
            _logger.error('missing entry')
            return False
        if len(self.entries[0].get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._activity.write_task_data('name', self.entries[0].get_text())

    def get_name(self):
        return self._name

    def get_graphics(self):
        self.entries = []
        graphics = Graphics()
        '''
        graphics.add_text(
            _('See that progress bar at the bottom of your screen?\n'
              'It fills up when you complete tasks.\n'
              'Complete tasks to earn badges...\n'
              "Earn all the badges and you’ll be XO-Certified!\n\n\n"
              'Time for the first task:\n'
              'Write your full name in the box below, then press Next.\n\n'),
            size=FONT_SIZES[self._font_size])
        '''
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'introduction2.html')
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        self.entries.append(graphics.add_entry())
        # graphics.add_text('\n\n')
        button = graphics.add_button(_('Next'),
                                     self._activity.task_button_cb)
        return graphics, button


class EnterEmailTask(Task):

    def __init__(self, activity):
        self._name = _('Enter Email Task')
        self.uid = 'enter-email-task'
        self.entries = []
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['enter-name-task']

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) == 0:
            _logger.error('missing entry')
            return False
        if len(self.entries[0].get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._activity.write_task_data('email_address',
                                       self.entries[0].get_text())

    def get_name(self):
        return self._name

    def get_graphics(self):
        self.entries = []
        target = self._activity.read_task_data('name').split()[0]
        graphics = Graphics()
        '''
        graphics.add_text(_('Nice work %s!\n'
                            "You’ve almost filled the bar!\n\n\n"
                            "Here’s another tricky one:\n"
                            'Write your email address in the box below, '
                            'then press Next\n\n' % target),
                          size=FONT_SIZES[self._font_size])
        '''
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html',
                            'introduction3.html?NAME=%s' % target)
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        self.entries.append(graphics.add_entry())
        # graphics.add_text('\n\n')
        button = graphics.add_button(_('Next'),
                                     self._activity.task_button_cb)
        return graphics, button


class ValidateEmailTask(Task):

    def __init__(self, activity):
        self._name = _('Validate Email Task')
        self.uid = 'validate-email-task'
        self.entries = []
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['enter-email-task']

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) < 2:
            _logger.error('missing entry')
            return False
        entry0 = self.entries[0].get_text()
        entry1 = self.entries[1].get_text()

        if len(entry0) == 0 or len(entry1) == 0:
            return False
        if entry0 != entry1:
            return False
        if '@' not in entry0:  # Need better validation
            return False
        if '.' not in entry0.split('@')[1]:
            return False
        return True

    def after_button_press(self):
        self._activity.write_task_data('email_address',
                                       self.entries[1].get_text())

    def get_name(self):
        return self._name

    def get_graphics(self):
        self.entries = []
        target = self._activity.read_task_data('email_address')
        graphics = Graphics()
        self.entries.append(graphics.add_entry(text=target))
        graphics.add_text('\n\n')
        graphics.add_text(
            _('Please confirm that you typed your\n'
              'email address correctly by typing it again below.\n\n'),
            size=FONT_SIZES[self._font_size])
        self.entries.append(graphics.add_entry())
        graphics.add_text('\n\n')
        button = graphics.add_button(_('Next'),
                                     self._activity.task_button_cb)
        return graphics, button


class BadgeOneTask(Task):
    def __init__(self, activity):
        self._name = _('Badge One')
        self.uid = 'badge-1'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['enter-name-task', 'enter-email-task', 'validate-email-task']

    def is_collectable(self):
        return False

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def after_button_press(self):
        target = self._activity.read_task_data('name').split()[0]
        self._activity._activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your first badge!" % target),
            icon='badge-intro')

    def test(self, exercises, task_data):
        return self._activity.button_was_pressed

    def get_graphics(self):
        name = self._activity.read_task_data('name')
        if name is not None:
            target = name.split()[0]
        else:
            target = ''
        graphics = Graphics()
        '''
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your first badge!\n\n" % target), bold=True,
            size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple tasks.\n'
              'Press Continue to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        '''
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html',
                            'introduction4.html?NAME=%s' % target)
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Continue'),
                                     self._activity.task_button_cb)
        return graphics, button


class ChangeNickTask(Task):

    def __init__(self, activity):
        self._name = _('Change Nick Task')
        self.uid = 'change-nick-task'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving nick value as %s' %
                          profile.get_nick_name())
            self._activity.write_task_data('nick', profile.get_nick_name())
            return False
        else:
            target = self._activity.read_task_data('nick')
            _logger.debug('%d attempt: comparing %s to %s' %
                          (task_data['attempt'], profile.get_nick_name(),
                           target))
            return not profile.get_nick_name() == target

    def after_button_press(self):
        _logger.error('how to jump to home view?')

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        def button_callback(widget):
            from jarabe.model import shell
            _logger.debug('My turn button clicked')
            shell.get_model().set_zoom_level(shell.ShellModel.ZOOM_HOME)

        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Help.activity', 'images', 'Home_fav-menu.png')
        graphics = Graphics()
        graphics.add_text(
            _('<b>Changing the Nickname</b>\n'
              "In this lesson we’re going to learn how to change our\n"
              'nickname on the XO.\n'
              'You entered your nickname on the screen shown below\n'
              'when you first started the XO up. Remember?\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        graphics.add_text(
            _('\n\n<b>What is the nickname?</b>\n'
              'The nickname is your name on the XO, and will appear\n'
              'all around Sugar as well as being visible on networks.\n\n'
              'Watch the animation below to see how it’s done:\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        graphics.add_text(
            _('\n\n<b>Step-by-step:</b>\n'
              '1. Go to the home screen\n'
              '2. Right click on the central icon\n'
              '3. Do other things\n'
              '4. Type in a new nickname\n'
              '5. Click yes to restart Sugar\n'
              '6. Reopen the One Academy activity to complete\n\n'
              '<b>Are you ready to try?</b>\n'
              'Watch the animation again if you like.\n'
              "When you’re ready to try, hit the \"My Turn\"\n"
              'button below to go to the home screen.\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_button(_('My turn'), button_callback)
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
        button = graphics.add_button(_('Continue'),
                                     self._activity.task_button_cb)
        return graphics, button


class ConfirmNickChangeTask(Task):

    def __init__(self, activity):
        self._name = _('Restore Nick Task')
        self.uid = 'confirm-nick-change-task'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['change-nick-task']

    def test(self, exercises, task_data):
        return self._activity.button_was_pressed

    def get_pause_time(self):
        return 1000

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        graphics = Graphics()
        graphics.add_text(
            _('Nice one!\n\n'
              'You changed your nickname to %s!' % profile.get_nick_name()),
            size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nYou can change it back any time you like.\n'
              'Press Continue to learn about the Frame.\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Continue'),
                                     self._activity.task_button_cb)
        return graphics, button


class BadgeTwoTask(Task):
    def __init__(self, activity):
        self._name = _('Badge Two')
        self.uid = 'badge-2'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['change-nick-task', 'confirm-nick-change-task']

    def is_collectable(self):
        return False

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def after_button_press(self):
        target = self._activity.read_task_data('name').split()[0]
        self._activity._activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your second badge!" % target),
            icon='badge-intro')

    def test(self, exercises, task_data):
        return self._activity.button_was_pressed

    def get_graphics(self):
        target = self._activity.read_task_data('name').split()[0]
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
              'Press Continue to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Continue'),
                                     self._activity.task_button_cb)
        return graphics, button


class AddFavoriteTask(Task):

    def __init__(self, activity):
        self._name = _('Add Favorite Task')
        self.uid = 'add-favorites-task'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving favorites list')
            favorites_list = get_favorites()
            self._activity.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = self._activity.read_task_data('favorites')
            return favorites_count > saved_favorites_count

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Help.activity', 'images',
                            'Journal_main_annotated.png')
        graphics = Graphics()
        graphics.add_text(_('Try adding a favorite to your homeview.\n\n'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        button = graphics.add_button(_('Next'),
                                     self._activity.task_button_cb)
        return graphics, button


class RemoveFavoriteTask(Task):

    def __init__(self, activity):
        self._name = _('Remove Favorite Task')
        self.uid = 'remove-favorites-task'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            favorites_list = get_favorites()
            self._activity.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = self._activity.read_task_data('favorites')
            return favorites_count < saved_favorites_count

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Help.activity', 'images',
                            'Journal_main_annotated.png')
        graphics = Graphics()
        graphics.add_text(
            _('Now try removing a favorite to your homeview.\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        button = graphics.add_button(_('Next'),
                                     self._activity.task_button_cb)
        return graphics, button


class BadgeThreeTask(Task):
    def __init__(self, activity):
        self._name = _('Badge Three')
        self.uid = 'badge-3'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['add-favorites-task', 'remove-favorites-task']

    def is_collectable(self):
        return False

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def after_button_press(self):
        target = self._activity.read_task_data('name').split()[0]
        self._activity._activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your third badge!" % target),
            icon='badge-intro')

    def test(self, exercises, task_data):
        return self._activity.button_was_pressed

    def get_graphics(self):
        target = self._activity.read_task_data('name').split()[0]
        graphics = Graphics()
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your third badge!\n\n" % target),
            bold=True, size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple '
              'tasks.\n'
              'Press Continue to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Continue'),
                                     self._activity.task_button_cb)
        return graphics, button


class FinishedAllTasks(Task):

    def __init__(self, activity):
        self._name = _('Finished All Tasks')
        self.uid = 'finished'
        self._activity = activity
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return []  # To Do: what tasks are actually required?

    def test(self, exercises, task_data):
        self._activity.completed = True
        return True

    def get_name(self):
        return self._name

    def get_graphics(self):
        graphics = Graphics()
        graphics.add_text(_('You are a Sugar Zenmaster.\n\n'),
                          size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Continue'),
                                     self._activity.task_button_cb)
        return graphics, button


class UITest(Task):

    def __init__(self, activity):
        self._name = _('UI Test Task')
        self.uid = 'uitest'
        self._activity = activity

    def test(self, exercises, task_data):
        return self._uitester()

    def _uitester(self):
        _logger.debug('uitree')
        _logger.debug(uitree.get_root())
        for node in uitree.get_root().get_children():
            _logger.debug('%s (%s)' % (node.name, node.role_name))
            for node1 in node.get_children():
                _logger.debug('> %s (%s)' % (node1.name, node1.role_name))
                for node2 in node1.get_children():
                    _logger.debug('> > %s (%s)' %
                                  (node2.name, node2.role_name))
        return True
