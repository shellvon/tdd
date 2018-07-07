# -*- coding:utf-8 -*-


import re

HELLO_REGEX = re.compile('^hello$', re.I)

# current plugin priority. optional. default is 0
PRIORITY = 10


def match(msg):
    return msg.type == 'text' and HELLO_REGEX.match(msg.content)


def response(msg, bot=None):
    return u'你好呀^_^'
