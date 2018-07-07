# -*- coding:utf-8 -*-

# current plugin priority. optional. default is 0
PRIORITY = 10


def match(msg):
    return msg.type == 'event' and msg.event == 'subscribe'


def response(msg, bot=None):
    return u'感谢大佬关注鄙人😊!, 您是第999位关注我的用户!'
