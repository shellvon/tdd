# -*- coding:utf-8 -*-

import re
import random

# 资源来自: https://iodefog.github.io/text/mviplist.json

PLATFORM_LST = [
    {"name": "爱奇艺", "url": "http://www.iqiyi.com/"},
    {"name": "腾讯视频", "url": "https://v.qq.com/"},
    {"name": "芒果", "url": "https://www.mgtv.com/"},
    {"name": "优酷", "url": "https://www.youku.com/"},
    {"name": "乐视视频", "url": "https://www.le.com/"},
    {"name": "搜狐视频", "url": "https://tv.sohu.com/"},
    {"name": "52影院", "url": "http://www.52xsba.com/"},
    {"name": "4080新视觉影院", "url": "http://www.yy4080.com/"}
]

PLAYER_LST = [
    {"name": "万能接口5", "url": "http://jx.vgoodapi.com/jx.php?url="},
    {"name": "5月-1", "url": "http://www.82190555.com/index/qqvod.php?url="},
    # {"name": "5月-2", "url": "http://jiexi.92fz.cn/player/vip.php?url="},
    {"name": "5月-3", "url": "http://api.wlzhan.com/sudu/?url="},
    # {"name": "5月-4", "url": "http://beaacc.com/api.php?url="},
    # {"name": "5月-8", "url": "http://api.visaok.net/?url="},
    {"name": "5月-9", "url": "http://api.xyingyu.com/?url="},
    # {"name": "5月-10", "url": "http://api.greatchina56.com/?url="},
    {"name": "5月-11", "url": "http://jx.618g.com/?url="},
    {"name": "5月-12", "url": "http://api.baiyug.vip/index.php?url="},
    {"name": "5月-14", "url": "http://api.xyingyu.com/?url="},
    # {"name": "5月-15", "url": "http://api.greatchina56.com/?url="},
    {"name": "5月-16", "url": "http://api.baiyug.vip/index.php?url="},
    {"name": "5月-17", "url": "http://api.visaok.net/?url="},
    {"name": "5月-18", "url": "http://jx.618g.com/?url="},
    # {"name": "5月-20", "url": "hhttp://api.baiyug.cn/vip/?url="},
    # {"name": "5月-21", "url": "http://jiexi.071811.cc/jx2.php?url="},
    {"name": "5月-22", "url": "http://www.82190555.com/index/qqvod.php?url="},
    {"name": "5月-24", "url": "http://www.82190555.com/index/qqvod.php?url="},
    {"name": "4.21-2", "url": "http://qtv.soshane.com/ko.php?url="},
    {"name": "4.21-3", "url": "https://yooomm.com/index.php?url="},
    {"name": "4.21-4", "url": "http://www.82190555.com/index.php?url="},
    {"name": "4.21-6", "url": "http://www.85105052.com/admin.php?url="},
    {"name": "高端解析", "url": "http://jx.vgoodapi.com/jx.php?url="},
    {"name": "六六视频", "url": "http://qtv.soshane.com/ko.php?url="},
    {"name": "超清接口1_0", "url": "http://www.52jiexi.com/tong.php?url="},
    {"name": "超清接口1_1", "url": "http://www.52jiexi.com/yun.php?url="},
    # {"name": "超清接口2", "url": "http://jiexi.92fz.cn/player/vip.php?url="},
    {"name": "品优解析", "url": "http://api.pucms.com/xnflv/?url="},
    {"name": "无名小站", "url": "http://www.82190555.com/index/qqvod.php?url="},
    # {"name": "腾讯可用，百域阁视频", "url": "http://api.baiyug.cn/vip/index.php?url="},
    {"name": "腾讯可用，线路三(云解析)", "url": "http://jiexi.92fz.cn/player/vip.php?url="},
    {"name": "腾讯可用，金桥解析", "url": "http://jqaaa.com/jx.php?url="},
    # {"name": "线路四（腾讯暂不可用）", "url": "http://api.nepian.com/ckparse/?url="},
    {"name": "线路五", "url": "http://aikan-tv.com/?url="},
    # {"name": "花园影视（可能无效）", "url": "http://j.zz22x.com/jx/?url="},
    {"name": "花园影视1", "url": "http://j.88gc.net/jx/?url="},
    {"name": "线路一(乐乐视频解析)", "url": "http://www.662820.com/xnflv/index.php?url="},
    {"name": "1717ty", "url": "http://1717ty.duapp.com/jx/ty.php?url="},
    {"name": "速度牛", "url": "http://api.wlzhan.com/sudu/?url="}, {"name": "1", "url": "http://17kyun.com/api.php?url="},
    {"name": "6", "url": "http://014670.cn/jx/ty.php?url="},
    {"name": "8", "url": "http://tv.x-99.cn/api/wnapi.php?id="}, {"name": "10", "url": "http://7cyd.com/vip/?url="},
    {"name": "表哥解析", "url": "http://jx.biaoge.tv/index.php?url="},
    {"name": "万能接口3", "url": "http://vip.jlsprh.com/index.php?url="},
    {"name": "万能接口4", "url": "https://api.daidaitv.com/index/?url="},
    {"name": "万能接口6", "url": "http://wwwhe1.177kdy.cn/4.php?pass=1&url="},
    {"name": "5月-5", "url": "http://www.ckplayer.tv/kuku/?url="},
    {"name": "5月-6", "url": "http://api.lvcha2017.cn/?url="}, {"name": "5月-7", "url": "http://www.aktv.men/?url="},
    {"name": "5月-13", "url": "http://jx.reclose.cn/jx.php/?url="},
    {"name": "5月-19", "url": "http://yun.baiyug.cn/vip/?url="},
    {"name": "5月-23", "url": "http://api.baiyug.cn/vip/index.php?url="},
    {"name": "5月-25", "url": "http://2gty.com/apiurl/yun.php?url="},
    {"name": "5月-26", "url": "http://v.2gty.com/apiurl/yun.php?url="},
    {"name": "4.21-5", "url": "http://jiexi.92fz.cn/player/vip.php?url="},
    {"name": "爱跟影院", "url": "http://2gty.com/apiurl/yun.php?url="}
]

__plugin__ = '播放器(VIP去广告)'
__description__ = '直接发送需要播放的视频地址[%s]即可,如果不行请尝试重复发送(每次返回的地址随机)' % ('|'.join(p['name'] for p in PLATFORM_LST))

URL_REGEX = re.compile(r'https?://[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,5}([-a-zA-Z0-9@:%_\+.~#?&//=]*)$')


def match(msg, bot=None):
    if msg.type != 'text':
        return False
    content = msg.content
    # 判断是不是一个完整的URL.
    if not URL_REGEX.match(content):
        return False

    for p in PLATFORM_LST:
        if p['url'] in content:
            return True

    return False


def response(msg, bot=None):
    source = random.choice(PLAYER_LST)
    return '帮您找了一个在线播放地址: {url}{link} , Powered By: {name}点击试试吧!\n\n注意:(如果提示被被封请复制此链接至浏览器打开或者重新尝试新的)'.format(
        link=msg.content, **source)


def main(url):
    source = random.choice(PLAYER_LST)
    print '帮你找了一个播放地址: {url}{link} , Powered By: {name}点击试试吧!(不行就再发我我重新找)'.format(link=url, **source)


if __name__ == '__main__':
    main('http://www.iqiyi.com/v_19rr0x6mik.html')
