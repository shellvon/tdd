# -*- coding:utf-8 -*-

import re
import time
import json
__plugin__ = '活动'
__description__ = '提供各种关键字/密钥进行相关活动回复'

# current plugin priority. optional. default is 0
PRIORITY = 10

activities = []

matched_activity = None


def bootstrap(bot=None):
    global activities
    try:
        with open('data/activity.json', 'rb') as f:
            activities = json.loads(f.read())
    except IOError, e:
        activities = []

def match(msg, bot=None):
    global matched_activity
    matched_activity = None
    if msg.type != 'text':
        return False
    content = msg.content
    now = time.time()
    for el in activities:
        pattern = el['keyword']
        if pattern[0] != '^' and pattern[-1] != '$':
            pattern = u'^{0}$'.format(pattern)
        if not re.match(pattern, content):
            continue
        if el['start'] <= now <= el['end']:
            matched_activity = el
            break
    return matched_activity is not None
   
def response(msg, bot=None):
    global matched_activity
    if not matched_activity:
        return
    resp = matched_activity['resp']
    if isinstance(resp, list):
        return u'\n'.join(resp)
    return resp
