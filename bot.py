# -*- coding:utf-8 -*-

import os
import urllib
import importlib
import pkgutil
import logging

from wechatpy import parse_message, create_reply
from wechatpy.replies import ImageReply, BaseReply
from werkzeug.contrib.cache import FileSystemCache

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
        self.cache = FileSystemCache('/tmp')
        self.client = None

    @property
    def wechat_client(self):
        return self.client

    @wechat_client.setter
    def wechat_client(self, client):
        self.client = client



    def _bootstrap_plugins(self):
        for plugin in self.plugins:
            if hasattr(plugin, 'bootstrap'):
                plugin.bootstrap(bot=self)
                logging.debug('%s triggered bootstrap', plugin.__name__)

    def nlp_chat(self, user, message):
        resp = self.ai.nlp_chat(user, message)
        if resp['ret'] == 0:
            return resp['data']['answer']
        logging.error(resp)
        return u'Sorry, 系统内部错了,错误代码: %s' % resp['msg']

    def get_current_img(self, msg):
        if msg.type != 'image':
            url = self.cache.get(msg.source + '_img_url')
        else:
            url = msg.image
        if not url:
            return
        return urllib.urlopen(url).read()

    def _media_upload(self, media_file, media_type='image'):
        if not self.wechat_client:
            return
        try:
            r = self.wechat_client.media.upload(media_file=media_file, media_type=media_type)
            return r['media_id']
        except Exception:
            return

    def image_resp(self, msg, resp):
        if resp['ret'] == 0:
            from cStringIO import StringIO
            import base64
            file_obj = StringIO(base64.b64decode(base64))
            # https://stackoverflow.com/questions/26300054/set-name-header-of-multipart-encoded-file-post
            mid = self._media_upload(media_file=('tmp.jpg', file_obj))
            if not mid:
                return create_reply('系统暂时不能处理此格式的图,请尝试其他图', msg)
            reply = ImageReply(
                media_id=mid,
                message=msg
            )
            # 本次步骤已经结束了,删除当前指令
            self.cache.delete(msg.source)
        else:
            reply = create_reply(resp['msg'], msg)
        return reply

    def face_age(self, msg):
        img = self.get_current_img(msg)
        resp = self.ai.ptu_faceage(img)
        return self.image_resp(msg, resp)

    def face_sticker(self, msg):
        # 获取当前的步骤.
        _filter = self.cache.get(msg.source + '_filter')
        if _filter is None or msg.type != 'text':
            return u'选择你需要的【大头贴】效果:\n 1.NewDay, 2. Enjoy\n'

        img = self.get_current_img(msg)
        resp = self.ai.ptu_facesticker(img, _filter)
        return self.image_resp(msg, resp)

    def face_merge(self, msg):
        # 获取当前的步骤.
        _filter = self.cache.get(msg.source + '_filter')
        if _filter is None or msg.type != 'text':
            return u'选择你需要的特效(回复:1-50)'
        img = self.get_current_img(msg)
        resp = self.ai.ptu_facemerge(img, _filter)
        return self.image_resp(msg, resp)

    def face_decoration(self, msg):
        # 获取当前的步骤.
        _filter = self.cache.get(msg.source + '_filter')
        if _filter is None or msg.type != 'text':
            return u'选择你需要的特效(回复:1-23)'
        img = self.get_current_img(msg)
        resp = self.ai.ptu_facedecoration(img, _filter)
        return self.image_resp(msg, resp)

    def face_cosmetic(self, msg):
        # 获取当前的步骤.
        _filter = self.cache.get(msg.source + '_filter')
        if _filter is None or msg.type != 'text':
            return u'选择你需要的特效(回复:1-)'
        img = self.get_current_img(msg)
        resp = self.ai.ptu_facecosmetic(img, _filter)
        return self.image_resp(msg, resp)

    def img_to_text(self, msg):
        img = self.get_current_img(msg)
        resp = self.ai.vision_image(img, msg.source)
        return self.image_resp(msg, resp)

    def img_filter(self, msg):
        _filter = self.cache.get(msg.source + '_filter')
        if _filter is None or msg.type != 'text':
            return u'选择你需要的【滤镜】效果(1-20):'
        img = self.get_current_img(msg)
        resp = self.ai.ptu_imagefilter(img, _filter)
        return self.image_resp(msg, resp)

    def exit(self, msg):
        self.cache.delete(msg.source)
        return u'👌'

    def img_fight(self, msg):
        self.cache.delete(msg.source)
        return u'暂时不支持斗图'

    @staticmethod
    def create_resp(resp, msg=None):
        if not resp:
            reply = create_reply('不好意思,目前我还无法处理您的消息,试试其他的吧.', msg)
        elif isinstance(resp, (str, unicode, tuple, list)):
            reply = create_reply(resp, msg)
        elif isinstance(resp, BaseReply):
            reply = resp
        else:
            reply = create_reply('我晕了～', msg)
        return reply.render()

    def response(self, request):
        msg = parse_message(request.data)
        for plugin in self.plugins:
            if plugin.match(msg):
                logging.debug('%s matched the msg: %s', plugin.__name__, msg)
                resp = plugin.response(msg, bot=self)
                if resp:
                    return resp
                logging.debug('消息没有返回,跳过用此插件(%s)处理', plugin.__name__)


        # 没有设置Command
        commands = {
            u'颜龄': self.face_age,
            u'大头贴': self.face_sticker,
            u'人脸融合': self.face_merge,
            u'滤镜': self.img_filter,
            u'人脸变妆': self.face_decoration,
            u'人脸美妆': self.face_cosmetic,
            u'看图说话': self.img_to_text,
            u'退出': self.exit,
            u'斗图': self.img_fight,
        }

        func_name = self.cache.get(msg.source)
        # 尝试从缓存中读到上一次的时间.
        command = commands.get(func_name)
        if command:
            return self.create_resp(command(msg), msg)

        if msg.type == 'text':
            command = commands.get(msg.content)
            # 如果当前环境没有指定command,则是聊天
            if not command:
                resp = self.nlp_chat(msg.source, msg.content)
            else:
                # 设置的当前的Command
                self.cache.set(msg.source, msg.content)
                resp = command(msg)
            return self.create_resp(resp, msg)

        if msg.type == 'image':
            # 记录当前的图片
            self.cache.set(msg.source+'_img_url', msg.image)
            infos = [
                '* 颜龄 : 查看您的年龄',
                '* 看图说话 : AI识别图的内容',
                '* 大头贴 : 选择数字(1-30)的一种大头贴特效'
                '* 滤镜 : 为您的照片增加一层滤镜',
                '* 人脸融合 : 古装/科幻等特效(特效支持1-50的范围)',
                '* 退出 : 退出上下文',
                '* 斗图 : 你懂的'
            ]
            return self.create_resp(u'收到一张图,你是要我做什么呢?\n\n %s' % ('\n'.join(infos)), msg)

        return self.create_resp(u'不支持的消息类型: %s' % msg.type, msg)


if __name__ == '__main__':
    import plugins as p
    print 'loaded plugins:', load_plugins(p)
