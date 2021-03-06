# -*- coding:utf-8 -*-

import re

__plugin__ = 'help'
__description__ = '输入<help>/<帮助>/<文档>/<功能>等尖括号内任意一单词查看此帮助信息'

REGEX = re.compile(u'^(help|帮助|功能|文档)$', re.I | re.U)

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


def match(msg, bot=None):
    return msg.type == 'text' and REGEX.match(msg.content)


def response(msg, bot=None):
    global all_plugins_info
    plugins = '\n\n'.join(['插件:{plugin}\n描述:{desc}'.format(**p) for p in all_plugins_info])
    return '您好,目前支持的系统功能您可以输入 <菜单> 或者<Menu> 进行查看(仅输入尖括号内的单词)， 另外，目前我们支持的功能插件有:\n%s' % plugins
