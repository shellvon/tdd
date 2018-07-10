# -*- coding:utf-8 -*-

import re
import random
import requests


from wechatpy.replies import ImageReply
from wechatpy.exceptions import WeChatClientException

__plugin__ = '斗图'
__description__ = '输入斗图 <关键词> 返回图片地址供您下载'

REGEX = re.compile(u'^斗图(\s\S+)?$', re.I | re.U)

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
        'keyword': keyword,
        'mime': 0,
        'page': 1, # random.choice([1,2,3]),
    }
    resp = requests.get(api, params=payloads, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'
    }).json()

    lst = resp['data']['list'] if resp['status'] == 1 else None

    if not lst:
        return
    from cStringIO import StringIO
    # 随机让每一次图尽可能不相同
    url = random.choice(lst)['image_url']
    r = re.search('(.{1,3}\.(?:jpe?g|png|gif))', url)
    if r:
        fname = r.group(1)
    else:
        fname = 'unknown.jpg'
    return fname, StringIO(requests.get(url).content)


def response(msg, bot=None):
    keyword = None
    if msg.type == 'text':
        keyword = msg.content.replace(u'斗图', '').strip()
    result = search(keyword)
    if not result or not bot:
        if bot:
            # 退出斗图.
            bot.cache.clear()
        return u'我败了,无图可战'
    try:
        result = bot.wechat_client.media.upload(media_type='image', media_file=result)
        mid = result['media_id']
        return ImageReply(message=msg, media_id=mid)
    except WeChatClientException, e:
        return u'我败了.....'


if __name__ == '__main__':
    print search('金馆长')