# -*- coding:utf-8 -*-

__plugin__ = '事件'
__description__ = '默认用于处理各类型的事件(如关注/取消关注/点击/拍照)'

# current plugin priority. optional. default is 0
PRIORITY = 10


def match(msg, bot=None):
    return msg.type == 'event'


def response(msg, bot=None):
    if msg.type != 'event':
        return 'Oops.'
    event = msg.event
    if event == 'subscribe':
        return u'感谢大佬关注鄙人😊!, 您是第998位关注我的用户!'
    if event == 'unsubscribe':
        return u'欢迎再来'
    if event == 'click':
        # TODO: 菜单.....
        key = msg.key
        return u'您点击了:%s' % key
    return u'暂时不支持此事件: %s' % event
