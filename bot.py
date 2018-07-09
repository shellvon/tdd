# -*- coding:utf-8 -*-

import urllib
import importlib
import pkgutil
import logging

from tencent.ai import AiPlat


def load_plugins(namespace):
    available_plugins = []
    for finder, name, ispkg in pkgutil.iter_modules(namespace.__path__, namespace.__name__ + '.'):
        module = importlib.import_module(name)
        if not hasattr(module, 'match') or not hasattr(module, 'response'):
            logging.warn('%s has no method:(match or repsonse), skipped it', name)
            continue
        available_plugins.append(module)
    return sorted(available_plugins, key=lambda x: getattr(x, 'PRIORITY', 0), reverse=True)


class AI(object):
    def __init__(self, api_id, api_key, plugins):
        self.plugins = plugins
        self.ai = AiPlat(api_id, api_key)
        self._bootstrap_plugins()

    def _bootstrap_plugins(self):
        for plugin in self.plugins:
            if hasattr(plugin, 'bootstrap'):
                logging.debug('plugin:%s has bootstrap', plugin)
                plugin.bootstrap(bot=self)

    def nlp_chat(self, user, message):
        resp = self.ai.nlp_chat(user, message)
        if resp['ret'] == 0:
            return resp['data']['answer']
        logging.error(resp)
        return u'Sorry, 系统内部错了,错误代码: %s' % resp['msg']

    def response(self, msg):
        for plugin in self.plugins:
            if plugin.match(msg):
                logging.debug('plugin:%s matched the msg: %s', plugin, msg)
                return plugin.response(msg, bot=self)
        logging.debug('No plugin matched.')
        if msg.type == 'text':
            return self.nlp_chat(msg.source, msg.content)
        if msg.type == 'image':
            try:
                img = urllib.urlopen(msg.image).read()
                resp = self.ai.vision_image(img, msg.source)
                if resp['ret'] != 0:
                    return resp['msg']
                return u'我猜测这张图的内容应该是: %s' % resp['data']['text']
            except:
                return u'我看不懂这张图....'
        return u'不支持的消息类型: %s' % msg.type


if __name__ == '__main__':
    import plugins as p
    print 'loaded plugins:', load_plugins(p)
