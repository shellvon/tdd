# -*- coding:utf-8 -*-

import re

REGEX = re.compile(u'^(help|帮助|菜单|功能|文档)$', re.I | re.U)

# current plugin priority. optional. default is 0
PRIORITY = 1


def match(msg):
    return msg.type == 'text' and REGEX.match(msg.content)


def response(msg, bot=None):
    funcs = [
        u'目前支持以下指令:',
        u'查看本文帮助: 输入 help|帮助|菜单|功能|文档 任意一个关键词',
        u'查找电影资源: 检索 <电影名/番号>',
        u'聊天/查看天气: 直接与我聊天即可',
        u'寻找优惠券: 淘宝分享给我(此功能已关闭)',
        u'智能识图: 发送图片给我,'
    ]
    return u'\n'.join(funcs)
