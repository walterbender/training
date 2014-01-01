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

import json
from gettext import gettext as _

from sugar3 import profile
from sugar3.test import uitree

import logging
_logger = logging.getLogger('training-activity-exercises')

ACCOUNT_NAME = 'mock'


class Exercises():

    def __init__(self, canvas, parent=None):
        self._activity = parent
        self._canvas = canvas
        self.completed = False
        _logger.error('__init__')

    def _run_task(self, msg, task, data):
        ''' To run a task, we need a message to display,
            a task method to call that returns True or False,
            and perhaps some data '''

        _logger.error('_run_task %d' % self._activity.current_task)

        task_key = 'task %d' % self._activity.current_task
        _logger.debug(self._activity.metadata)
        if task_key in self._activity.metadata:
            task_data = json.loads(self._activity.metadata[task_key])
            _logger.debug(task_data)
        else:
            self._activity.alert_task(msg=msg)
            _logger.debug('first time on task')
            task_data = {}
            task_data['task'] = msg
            task_data['attempt'] = 0
            task_data['data'] = data
        if task(self, task_data):
            _logger.debug('success %d' % self._activity.current_task)
            self._activity.alert_task(
                title=_('Congratulations'),
                msg=_('You successfully completed your task.'))
            self._activity.current_task += 1
            self._activity.metadata['current task'] = \
                str(self._activity.current_task)
            if not self.completed:
                self.task_master()
            else:
                self._activity.alert_task(
                    title=_('Congratulations'),
                    msg=_('All tasks completed.'))
        else:
            task_data['attempt'] += 1
            _logger.debug('keep trying')
            self._activity.alert_task(
                title=_('Keep trying'),
                msg=msg)

        self._activity.metadata[task_key] = json.dumps(task_data)

    def task_master(self):
        _logger.error('task_master')

        if self._activity.current_task == 0:

            def task(self, task_data):
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

            _logger.error('calling _run_task with %s' %
                          _('Change your nick'))
            self._run_task(_('Change your nick'), task, None)

        if self._activity.current_task == 1:

            def task(self, task_data):
                result = profile.get_nick_name() == \
                    self._activity.metadata['nick']
                if result:
                    self._activity.add_badge(
                        _('Congratulations! You changed your nickname.'))
                return result

            _logger.error('calling _run_task with %s' %
                          _('Change your nick back'))
            self._run_task(_('Change your nick back'), task, None)

        if self._activity.current_task == 2:

            def task(self, task_data):
                if task_data['attempt'] == 0:
                    _logger.debug('first attempt: saving favorites list')

                    favorites_list = get_favorites()
                    self._activity.metadata['favorites'] = \
                        json.dumps(favorites_list)
                    return False
                else:
                    favorites_list = get_favorites()
                    saved_favorites = \
                        json.loads(self._activity.metadata['favorites'])
                    return len(favorites_list) > len(saved_favorites)

            self._run_task(_('Add a favorite'), task, None)

        if self._activity.current_task == 3:

            def task(self, task_data):
                if task_data['attempt'] == 0:
                    _logger.debug('first attempt: saving favorites list')

                    favorites_list = get_favorites()
                    self._activity.metadata['favorites'] = \
                        json.dumps(favorites_list)
                    return False
                else:
                    favorites_list = get_favorites()
                    saved_favorites = \
                        json.loads(self._activity.metadata['favorites'])
                    result = len(favorites_list) < len(saved_favorites)
                    if result:
                        self._activity.add_badge(
                            _('Congratulations! You changed your '
                              'favorite activities.'))
                    return result

            self._run_task(_('Remove a favorite'), task, None)

        if self._activity.current_task == 4:

            def task(self, task_data):
                return True

            _logger.error('calling _run_task with %s' %
                          _('Mission accomplished'))

            self.completed = True
            self._run_task(_('You are a Sugar Zen master.'), task, None)

        if self._activity.current_task == 5:
            self.completed = True
            self._activity.alert_task(
                title=_('Congratulations'),
                msg=_('All tasks completed.'))

            '''
            try:
                yield
            except:
                _logger.debug('except')
                _logger.debug(uitree.get_root().dump())
                raise
            finally:
                _logger.debug('finally')
            '''

        _logger.error('...')


def get_favorites():
    from sugar3 import env
    import os

    favorites_path = env.get_profile_path('favorite_activities')
    if os.path.exists(favorites_path):
        favorites_data = json.load(open(favorites_path))
        favorites_list = favorites_data['favorites']
    return favorites_list
