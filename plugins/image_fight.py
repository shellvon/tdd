# -*- coding:utf-8 -*-

import re
import random
import requests


from wechatpy.replies import ImageReply
__plugin__ = '斗图'
__description__ = '输入斗图 <关键词> 返回图片地址供您下载'

REGEX = re.compile(u'^斗图 .+$', re.I | re.U)

# current plugin priority. optional. default is 0
PRIORITY = 1


def match(msg, bot=None):
    # 判断是否退出
    if msg.type == 'text' and (msg.content == u'退出' or msg.content.lower() == 'exit'):
        return False
    # 判断当前的command是否为斗图.
    if bot.cache.get(msg.source) == 'img_fight':
        return True
    # 判断是否开启斗图
    r = msg.type == 'text' and REGEX.match(msg.content)
    if r:
        bot.cache.set(msg.source, 'img_fight')
    return r


def search(keyword=None):
    if not keyword:
        keyword = random.choice([u'金馆长', u'暴走', u'明明'])
    api = 'https://www.doutula.com/api/search'
    payloads = {
        'search': keyword,
        'mime': 0,
        'page': random.choice([1,2,3]),
    }
    lst = requests.get(api, params=payloads).json()['data']['list']
    if not lst:
        return
    from cStringIO import StringIO
    # 随机让每一次图尽可能不相同
    url = random.choice(lst)['image_url']
    r = re.search('(\.(?:jpe?g|png|gif))', url)
    if r:
        fname = r.group(1)
    else:
        fname = 'unknown.jpg'
    return fname, StringIO(requests.get(url).raw)


def response(msg, bot=None):
    keyword = None
    if msg.type == 'text':
        keyword = msg.content.split()[1]
    result = search(keyword)
    if not result or not bot:
        return u'我败了,无图可战'
    mid = bot.wechat_client.upload(media_file=result)
    return ImageReply(message=msg, media_id=mid).render()


