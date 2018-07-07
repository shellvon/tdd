# -*- coding:utf-8 -*-

import urllib
import importlib
import pkgutil
import logging

from tencent.ai import AiPlat


def load_plugins(namespace):
    plugins = []
    for finder, name, ispkg in pkgutil.iter_modules(namespace.__path__, namespace.__name__ + '.'):
        module = importlib.import_module(name)
        if not hasattr(module, 'match') or not hasattr(module, 'response'):
            logging.warn('%s has no method:(match or repsonse), skipped it', name)
            continue
        if hasattr(module, 'PRIORITY'):
            priority = getattr(module, 'PRIORITY')
        else:
            priority = 0
        plugins.append((priority, name, module))
    return sorted(plugins, key=lambda x: x[0], reverse=True)


class AI(object):
    def __init__(self, api_id, api_key, plugins):
        self._plugins = plugins
        self.ai = AiPlat(api_id, api_key)

    def nlp_chat(self, user, message):
        resp = self.ai.nlp_chat(user, message)
        if resp['ret'] == 0:
            return resp['data']['answer']
        logging.error(resp)
        return u'Sorry, 系统内部错了,错误代码: %s' % resp['msg']

    def response(self, msg):
        for (priority, name, plugin) in self._plugins:
            if plugin.match(msg):
                logging.debug('%s matched the msg: %s', name, msg)
                return plugin.response(msg, bot=self)
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
