# -*- coding: utf-8 -*-
# Copyright (c) 2013 Walter Bender

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

from sugar3 import profile
from sugar3.test import uitree

import logging
_logger = logging.getLogger('training-activity-exercises')

ACCOUNT_NAME = 'mock'


def get_favorites():
    from sugar3 import env
    import os

    favorites_path = env.get_profile_path('favorite_activities')
    if os.path.exists(favorites_path):
        favorites_data = json.load(open(favorites_path))
        favorites_list = favorites_data['favorites']
    return favorites_list


class Exercises():

    def __init__(self, activity):
        self._activity = activity
        self._current_task = None
        self.completed = False

        self._task_list = [ChangeNickTask(self._activity),
                           RestoreNickTask(self._activity),
                           AddFavoriteTask(self._activity),
                           RemoveFavoriteTask(self._activity),
                           FinishedAllTasks(self._activity)]

    def _run_task(self, task_number):
        ''' To run a task, we need a message to display,
            a task method to call that returns True or False,
            and perhaps some data '''

        if task_number < len(self._task_list):
            msg = self._task_list[task_number].get_prompt()
            success = self._task_list[task_number].get_success()
            retry = self._task_list[task_number].get_retry()
            data = self._task_list[task_number].get_data()
            test = self._task_list[task_number].test
            uid = self._task_list[task_number].uid

            _logger.error('_run_task %d' % self._activity.current_task)

            task_key = 'task %d' % self._activity.current_task
            _logger.debug(self._activity.metadata)
            
            task_data = self._activity.read_task_data(uid)
            if task_data is None:
                self._activity.alert_task(msg=msg)
                _logger.debug('first time on task %s' % (msg))
                task_data = {}
                task_data['task'] = msg
                task_data['attempt'] = 0
                task_data['data'] = data
            if test(self, task_data):
                _logger.debug('success %d' % self._activity.current_task)
                self._activity.alert_task(
                    title=_('Congratulations'),
                    msg=success)
                self._activity.current_task += 1
                self._activity.metadata['current task'] = \
                    str(self._activity.current_task)
                if not self.completed:
                    self.task_master()
            else:
                task_data['attempt'] += 1
                _logger.debug(retry)
                self._activity.alert_task(title=retry, msg=msg)
            self._activity.write_task_data(uid, task_data)
        else:
            self.completed = True
            self._activity.alert_task(
                title=_('Congratulations'),
                msg=_('All tasks completed.'))

    def task_master(self):
        _logger.debug('task_master')
        self._run_task(self._activity.current_task)
        _logger.debug('...')


class Task():
    ''' Generate class for defining tasks '''

    def __init__(self, activity):
        self.name = 'Generic Task'
        self.uid = None
        self._activity = activity

    def test(self, exercises, task_data):
        ''' The test to determine if task is completed '''
        raise NotImplementedError

    def get_success(self):
        ''' String to present to the user when task is completed '''
        return _('Success!')

    def get_retry(self):
        ''' String to present to the user when task is not completed '''
        return _('Keep trying')

    def get_data(self):
        ''' Any data needed for the test '''
        return None

    def get_prompt(self):
        ''' String to present to the user to define the task '''
        raise NotImplementedError

    def get_graphics(self):
        ''' A box containing graphics to present with the task '''
        return Gtk.Box()


class ChangeNickTask(Task):

    def __init__(self, activity):
        self.name = _('Change Nick Task')
        self.uid = 'nick1'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving nick value as %s' % 
                          profile.get_nick_name())
            self._activity.metadata['nick'] = profile.get_nick_name()
            return False
        else:
            _logger.debug('%d attempt: comparing %s to %s' % 
                          (task_data['attempt'],
                           profile.get_nick_name(),
                           self._activity.metadata['nick']))
            return not profile.get_nick_name() == \
                self._activity.metadata['nick']

    def get_prompt(self):
        return _('Change your nick')


class RestoreNickTask(Task):

    def __init__(self, activity):
        self.name = _('Restore Nick Task')
        self.uid = 'nick2'
        self._activity = activity

    def test(self, exercises, task_data):
        result = profile.get_nick_name() == self._activity.metadata['nick']
        if result:
            self._activity.add_badge(
                _('Congratulations! You changed your nickname.'))
        return result

    def get_prompt(self):
        return _('Restore your nick to %s' % (self._activity.metadata['nick']))


class AddFavoriteTask(Task):

    def __init__(self, activity):
        self.name = _('Add Favorite Task')
        self.uid = 'favorites1'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving favorites list')
            favorites_list = get_favorites()
            self._activity.metadata['favorites'] = json.dumps(favorites_list)
            return False
        else:
            favorites_list = get_favorites()
            saved_favorites = json.loads(self._activity.metadata['favorites'])
            return len(favorites_list) > len(saved_favorites)

    def get_prompt(self):
        return _('Add a favorite')


class RemoveFavoriteTask(Task):

    def __init__(self, activity):
        self.name = _('Remove Favorite Task')
        self.uid = 'favorites2'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            favorites_list = get_favorites()
            self._activity.metadata['favorites'] = json.dumps(favorites_list)
            return False
        else:
            favorites_list = get_favorites()
            saved_favorites = json.loads(self._activity.metadata['favorites'])
            result = len(favorites_list) < len(saved_favorites)
            if result:
                self._activity.add_badge(
                    _('Congratulations! You changed your '
                      'favorite activities.'))
            return result

    def get_prompt(self):
        return _('Remove a favorite')


class FinishedAllTasks(Task):

    def __init__(self, activity):
        self.name = _('Finished All Tasks')
        self.uid = 'finished'
        self._activity = activity

    def test(self, exercises, task_data):
        return True

    def get_prompt(self):
        return _('You are a Sugar Zen master.')
