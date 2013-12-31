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

    def __init__(self, canvas, parent=None, mycolors=['#A0FFA0', '#FF8080']):

        self._activity = parent
        self._canvas = canvas

        self._task_master()

    def _task_master(self):
        _logger.debug(self._activity.current_task)
        
        if self._activity.current_task == 0:
            _logger.debug('0')
            task_key = 'task %d' % self._activity.current_task
            _logger.debug('change your nick')
            self._activity.alert_task(_('Change your nick'))
            if task_key in self._activity.metadata:
                task_data = json.loads(self._activity.metadata[task_key])
                _logger.debug(task_data)
                _logger.debug('target is *not* %s' %
                              self._activity.metadata['nick'])
                if 'data' in task_data:
                    if task_data['data'] == profile.get_nick_name():
                        _logger.debug('try again')
                        task_data['attempt'] += 1
                    else:
                        _logger.debug('success %d' %
                                      self._activity.current_task)
                        self._activity.current_task += 1
                        self._activity.metadata['current task'] = \
                            str(self._activity.current_task)
                        self._task_master()
                else:
                    _logger.debug('bad task data???')
            else:
                _logger.debug('first time on task')
                task_data = {}
                self._activity.metadata['nick'] = \
                    task_data['data'] = profile.get_nick_name()
                task_data['task'] = 'change your nick'
                task_data['attempt'] = 0
            self._activity.metadata[task_key] = json.dumps(task_data)

        if self._activity.current_task == 1:
            _logger.debug('1')
            task_key = 'task %d' % self._activity.current_task
            _logger.debug('change your nick back')
            self._activity.alert_task(_('Change your nick back'))
            if task_key in self._activity.metadata:
                task_data = json.loads(self._activity.metadata[task_key])
                _logger.debug(task_data)
                _logger.debug('target is %s' %
                              self._activity.metadata['nick'])
                if profile.get_nick_name() != self._activity.metadata['nick']:
                    _logger.debug('try again')
                    task_data['attempt'] += 1
                else:
                    _logger.debug('success %d' %
                                  self._activity.current_task)
                    self._activity.current_task += 1
                    self._activity.metadata['current task'] = \
                        str(self._activity.current_task)
                    self._task_master()
            else:
                _logger.debug('first time on task')
                task_data = {}
                task_data['task'] = 'change your nick back'
                task_data['attempt'] = 0
                task_data['data'] = profile.get_nick_name()
            self._activity.metadata[task_key] = json.dumps(task_data)

        if self._activity.current_task == 2:
            import time
            _logger.debug('2')
            _logger.debug('Cool. All done.')
            self._activity.alert_task(_('Cool. You are a Sugar Zen master.'))

            _logger.error('going to sleep')
            # time.sleep(3)
            try:
                yield
            except:
                _logger.debug('except')
                _logger.debug(uitree.get_root().dump())
                raise
            finally:
                _logger.debug('finally')

            '''
            for name in ['Clipboard', ACCOUNT_NAME]:

                _logger.debug(root.find_child(name=name, role_name='menu item'))
            '''
