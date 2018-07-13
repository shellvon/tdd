# -*- coding:utf-8 -*-

import re
import requests

__plugin__ = '检索'
__description__ = '输入<检索 关键词> 进行查询,其中关键词可以是演员名/电影名等信息(最多返回3条信息)'

# current plugin priority. optional. default is 0
PRIORITY = 10


def match(msg, bot=None):
    if msg.type != 'text':
        return False
    data = msg.content.split(' ')
    return len(data) == 2 and data[0] == u'检索'


def search(keywords):
    api = 'https://www.torrentkitty.tv/search'
    regex = 'href="/information/(.{40})" title="([^\"]+)"'
    resp = requests.get('%s/%s/1' % (api, keywords), headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'}).content
    result = re.findall(regex, resp)
    return result[:3] if result else []


def response(msg, bot=None):
    keyword = msg.content.split(' ')[1]
    result = search(keyword)
    if not result:
        return u'找不到您要的资源啦😢'
    return u'======\n'.join([u'【资源】: %s\n 【Key】: %s\n' % (el[1].decode('utf8'), el[0]) for el in result])


def main():
    print search(u'钢铁侠')


if __name__ == '__main__':
    main()
