# -*- coding:utf-8 -*-

__plugin__ = '事件'
__description__ = '默认用于处理各类型的事件(如关注/取消关注/点击/拍照)'

# current plugin priority. optional. default is 0
PRIORITY = 10


def match(msg, bot=None):
    return msg.type == 'event'


def response(msg, bot=None):
    if msg.type != 'event':
        return 'Oops.'
    event = msg.event
    if event == 'subscribe' or event == 'subscribe_scan':
        return """嘿，我亲爱的朋友，终于等到你，您是第 998 位关注我的，非常谢谢！
        淘逗逗致力于淘互联网上最有趣的图摘，最实用的软件，最神器的网站，只为让你生活更有趣。
        
        淘逗逗通常在周一至周六为您推荐12张趣图(含笑话或者视频)
        
        您可以输入     <菜单>/<Menu> 进行查看我目前支持的功能。
        您也可以输入好 <help>/<帮助>/<文档>/<功能> 词语查看我支持的插件功能。
        
        以上关键字均不包含尖括号内本身。
        """
    if event == 'unsubscribe':
        return '欢迎再来'
    if event == 'click':
        # TODO: 菜单.....
        key = msg.key
        return '您点击了:%s' % key
    return '暂时不支持此事件: %s' % event
