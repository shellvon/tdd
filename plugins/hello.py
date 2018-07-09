# -*- coding:utf-8 -*-


import re

__plugin__ = 'hello_world'
__description__ = '发送hello,回复你好呀'

HELLO_REGEX = re.compile('^hello$', re.I)

# current plugin priority. optional. default is 0
PRIORITY = 10


def match(msg):
    return msg.type == 'text' and HELLO_REGEX.match(msg.content)


def response(msg, bot=None):
    return u'你好呀^_^'
