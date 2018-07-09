# -*- coding:utf-8 -*-

import re

__plugin__ = 'help'
__description__ = '输入帮助/文档等关键词查看帮助信息'

REGEX = re.compile(u'^(help|帮助|菜单|功能|文档)$', re.I | re.U)

# current plugin priority. optional. default is 0
PRIORITY = 1

all_plugins_info = []


def bootstrap(bot=None):
    if not hasattr(bot, 'plugins'):
        return
    global all_plugins_info
    all_plugins_info = [
        {
            'plugin': getattr(p, '__plugin__', ''),
            'desc': getattr(p, '__description__', 'Unknown')
        } for p in bot.plugins]


def match(msg):
    return msg.type == 'text' and REGEX.match(msg.content)


def response(msg, bot=None):
    global all_plugins_info
    plugins = '\n'.join(['插件:{name}\n描述:{desc}' for p in all_plugins_info])
    return '您好,目前我们支持的功能插件有:\n%s' % plugins
