# -*- coding:utf-8 -*-

import re
import sys
import time
import logging
from os import path

import requests

pdir = path.dirname(path.dirname(path.abspath(__file__)))

sys.path.insert(0, pdir)

from setting import TB_COOKIE_STR


__plugin__ = '优惠券'
__description__ = '将商品消息发送至公众号'


def match(msg, bot=None):
    if msg.type != 'text':
        return False
    content = msg.content
    return parse_tb_token(content, only_verify=True)


def bootstrap(bot=None):
    pass


def parse_tb_token(content, only_verify=False):
    patt = u'【(?P<title>.+?)】(?P<url>http://[^ ]+)?.*(?P<token>(€)[a-zA-Z\d]+\\4)'
    matched = re.search(patt, content, re.U | re.I | re.X)
    if only_verify:
        return matched is None
    if not matched:
        return
    # extract more details.
    info = matched.groupdict()
    if info['url'] is None:
        info['url'] = get_short_link_by_token(info['token'])
    print info
    item_id = get_item_id_from_short_link(info['url'])
    info['url'] = 'https://detail.tmall.com/item.htm?id=%s' % item_id
    return info


def get_item_id_from_short_link(link):
    patt = r'^https?://a\.m\.taobao\.com/.(\d+).htm'
    r = re.search(patt, link)
    if r:
        return r.group(1)
    r = re.search(r'^https?://item\.taobao\.com/item\.htm?.*(?:[&\?])id=(\d+)', link)
    if r:
        return r.group(1)

    # 尝试发起请求之后看请求题内的id
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }

    resp = requests.get(link, headers=headers).content
    r = re.search(patt, resp)
    if r:
        return r.group(1)
    logging.error('extract item_id failed from link:%s', link)


def get_short_link_by_token(tb_token):
    api = 'http://www.taokouling.com/index.php?m=api&a=taokoulingjm'
    payloads = {'username': 'wx_tb_fanli', 'password': 'wx_tb_fanli', 'text': tb_token}
    resp = requests.post(api, data=payloads).json()
    url = resp.get('url')
    logging.debug('extract short link by token: %s', url)
    return url


def get_coupon(auth_info, q):
    alimama = Alimama(cookie_str=auth_info)
    if not alimama.check_login():
        raise AuthException
    info = alimama.get_tbk_link(q)
    if not info:
        return
    coupon_short_url = info.get('couponShortLinkUrl')
    product_short_url = info.get('shortLinkUrl')
    coupon_token = info.get('couponLinkTaoToken')
    taobao_token = info.get('taoToken')
    coupon_amount = info.get('couponAmount')
    product_price = info.get('zkPrice')
    product_name = info.get('title')
    return {
        'token': coupon_token if coupon_token else taobao_token,
        'coupon': coupon_amount,
        'price': product_price,
        'name': product_name,
        'link': coupon_short_url if coupon_short_url else product_short_url,
    }


def response(msg, bot=None):
    token_info = parse_tb_token(msg.content)
    if not token_info:
        return u'无法成功解析您的输入'
    try:
        coupons = get_coupon(TB_COOKIE_STR, token_info['url'])
    except AuthException:
        return u'此服务暂时关闭,如果需要请联系管理员'
    except:
        return u'服务暂时不可用😫...'
    if not coupons:
        return u'找不到您要的商品(开发大大正在优化中...需要耐心等待)'
    resp = u'''【商品】{name}
【优惠券】{coupon}元
 请复制{token}淘口令、打开淘宝APP下单
-----------------
【下单地址】{link}'''.format(**coupons)
    return resp


class AuthException(Exception):
    pass


class Alimama(object):
    base_uri = 'http://pub.alimama.com'

    def __init__(self, cookie_str):
        self.req = requests.Session()
        self.req.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Referer': 'http://pub.alimama.com',
            #  'Cookie': cookie_str,
            'Connection': 'close'
        })

        self.req.cookies.update(
            {
                k.strip(): v for k, v in re.findall('(.*?)=(.*?);', cookie_str)
            }
        )

    def check_login(self):
        end_point = '/common/getUnionPubContextInfo.json'
        resp = self.req.get('%s%s' % (self.base_uri, end_point)).json()
        return resp['ok'] and ('mmNick' in resp['data'])

    @property
    def curtime(self):
        return str(int(time.time()) * 1000)

    @property
    def tb_token(self):
        token = self.req.cookies.get('_tb_token_')
        return token if token else ''

    def search(self, q):
        end_point = '/items/search.json'
        payloads = {
            'q': q,
            't': self.curtime,
            'shopTag': 'yxjh',  # 包含营销计划
            '_tb_token_': self.tb_token
        }
        resp = self.req.get('%s%s' % (self.base_uri, end_point), params=payloads).json()
        products = []
        if resp['ok'] and ('pageList' in resp['data']):
            products = resp['data']['pageList']
        else:
            logging.warn('resp failed: %s', resp)
        return products

    def get_tbk_link(self, q):
        products = self.search(q)
        if not products:
            return
        product = products[0]
        adzone_info = self.get_adzone(product['auctionId'])
        if not adzone_info:
            return
        resp = self.create_adzone(**adzone_info)
        if not resp:
            logging.error('create adzone failed!')
            return
        auction_code = self.get_auction_code(
            auction_id=product.get('auctionId'),
            adzone_id=resp.get('adzoneId'),
            site_id=resp.get('siteId'))
        if not auction_code:
            return
        # 提取部分想要的信息.
        details = {
            'title': product['title'],
            'couponAmount': product['couponAmount'],
            'couponInfo': product['couponInfo'],
            'couponStartFee': product['couponStartFee'],
            'zkPrice': product['zkPrice'],
            'couponFeftCount': product['couponLeftCount'],
        }

        details.update(auction_code)
        return details

    def get_adzone(self, item_id):
        '''获取广告位'''
        end_point = '/common/adzone/newSelfAdzone2.json'
        payloads = {
            'tag': 29,
            'itemId': item_id,
            't': self.curtime
        }
        resp = self.req.get('%s%s' % (self.base_uri, end_point), params=payloads)
        if resp.status_code != 200:
            return
        resp = resp.json()
        if not resp['ok']:
            logging.warn('无法获取广告位信息')
            return
        info = resp['data']['otherList']
        zone = resp['data']['otherAdzones']
        if info and zone:
            return {
                'zone_id': zone[0]['sub'][0]['id'],
                'site_id': info[0]['siteid'],
                'gcid': info[0]['gcid']
            }

    def create_adzone(self, zone_id=None, site_id=None, gcid=None):
        payloads = {
            'tag': 29,
            'gcid': gcid,
            'siteid': site_id,
            'selectact': 'sel',
            'adzoneid': zone_id,
            't': self.curtime,
            '_tb_token_': self.tb_token,
        }
        end_point = '/common/adzone/selfAdzoneCreate.json'
        headers = {}
        resp = self.req.post('%s%s' % (self.base_uri, end_point), data=payloads, headers=headers).json()
        return resp.get('data')

    def get_auction_code(self, auction_id=None, adzone_id=None, site_id=None):
        end_point = '/common/code/getAuctionCode.json'
        payloads = {
            'auctionid': auction_id,
            'adzoneid': adzone_id,
            'siteid': site_id,
            'scenes': 1,
            '_tb_token_': self.tb_token,
        }
        resp = self.req.get('%s%s' % (self.base_uri, end_point), params=payloads).json()
        if resp['ok']:
            return resp['data']
        logging.error('get_auction_code failed: resp=>%s', resp)

    def keep_login(self):
        # TODO: 怎么刷新 Cookie ?
        start = time.time()
        while self.check_login():
            try:
                self.req.get('http://pub.alimama.com/')
            except:
                pass
            time.sleep(10)
        logging.error('Sorry, Cookie Expired: %.2f', time.time() - start)


def main():
    info = parse_tb_token(u'【原创手绘插画iphone x手机壳硅胶6s软苹果8plus文艺情侣7p手机套】，復·制这段描述€klsm0AmrHM1€后到👉淘♂寳♀👈')
    print info
    print get_coupon(TB_COOKIE_STR, info['url'])


if __name__ == '__main__':
    main()
