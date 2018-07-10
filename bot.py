# -*- coding:utf-8 -*-

import base64
import urllib
import importlib
import pkgutil
import logging
from cStringIO import StringIO

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


def enum(**kwargs):
    return type('Enum', (), kwargs)


class AI(object):
    COMMANDS = enum(
        EXIT='exit',  # 退出
        CHAT='nlp_chat',  # 聊天
        AGE='face_age',  # 颜龄
        STICKER='face_sticker',  # 大头贴
        MERGE='face_merge',  # 人脸融合
        DECORATION='face_decoration',  # 变妆
        COSMETIC='face_cosmetic',  # 美妆
        FILTER='image_filter',  # 滤镜
        IMG_TO_TEXT='img_to_text',  # 看图说话
        MENU='menus',  # 菜单.
    )

    def __init__(self, api_id, api_key, plugins):
        self.plugins = plugins
        self.ai = AiPlat(api_id, api_key)
        self._bootstrap_plugins()
        self.cache = FileSystemCache('/tmp/wechat-bot-cache')
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

    def nlp_chat(self, msg):
        """普通的文本聊天"""
        if msg.type != 'text':
            return u'无法处理此消息类型:<%s>' % msg.type

        resp = self.ai.nlp_chat(msg.source, msg.content)
        if resp['ret'] == 0:
            return resp['data']['answer']
        return u'Sorry, 系统内部错了,错误信息: %s' % resp['msg']

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
        except Exception, e:
            logging.error('upload image failed! => %s', e)
            return

    def image_resp(self, msg, resp):
        if resp['ret'] == 0:
            file_obj = StringIO(base64.b64decode(resp['data']['image']))
            # https://stackoverflow.com/questions/26300054/set-name-header-of-multipart-encoded-file-post
            mid = self._media_upload(media_file=('tmp.jpg', file_obj))
            if not mid:
                return create_reply('系统暂时不能处理此格式的图,请尝试其他图!', msg)
            reply = ImageReply(
                media_id=mid,
                message=msg
            )
            # 本次步骤已经结束了,删除当前指令
            self.cache.delete(msg.source)
        else:
            reply = create_reply(u'%s, 重新上传一张图试试吧!' %resp['msg'], msg)
        return reply

    def face_age(self, msg):
        img = self.get_current_img(msg)
        resp = self.ai.ptu_faceage(img)
        return self.image_resp(msg, resp)

    def reply_help_img(self, msg, file):
        mid = self._media_upload(media_file=file)
        if not mid:
            return u'请回复你要的特效编号:1-30'
        return ImageReply(
            media_id=mid,
            message=msg
        )

    def face_sticker(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/sticker.png', 'rb'))
        img = self.get_current_img(msg)
        resp = self.ai.ptu_facesticker(img, msg.content)
        return self.image_resp(msg, resp)

    def face_merge(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/merge.png', 'rb'))
        img = self.get_current_img(msg)
        resp = self.ai.ptu_facemerge(img, msg.content)
        return self.image_resp(msg, resp)

    def face_decoration(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/decoration.png', 'rb'))
        img = self.get_current_img(msg)
        resp = self.ai.ptu_facedecoration(img, msg.content)
        return self.image_resp(msg, resp)

    def face_cosmetic(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/cosmetic.png', 'rb'))
        img = self.get_current_img(msg)
        resp = self.ai.ptu_facecosmetic(img, msg.content)
        return self.image_resp(msg, resp)

    def img_to_text(self, msg):
        img = self.get_current_img(msg)
        resp = self.ai.vision_image(img, msg.source)
        return self.image_resp(msg, resp)

    def img_filter(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/filter.png', 'rb'))
        img = self.get_current_img(msg)
        resp = self.ai.ptu_imagefilter(img, msg.content)
        return self.image_resp(msg, resp)

    def exit(self, msg):
        r = self.cache.clear()
        return u'已退出👌 欢迎下次再聊!(code: %s)' % r

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

    def parse_command(self, msg):
        command = self.cache.get(msg.source)
        if command:
            logging.debug('command from history(cached): %s', command)
            return command

        command = self.COMMANDS.CHAT
        if msg.type == 'text':
            content = msg.content.lower()
            if content == u'颜龄' or content == 'age':
                command = self.COMMANDS.AGE
            elif content == u'大头贴' or content == 'sticker':
                command = self.COMMANDS.STICKER
            elif content == u'人脸融合' or content == 'merge':
                command = self.COMMANDS.MERGE
            elif content == u'聊天' or content == 'chat':
                command = self.COMMANDS.CHAT
            elif content == u'看图说话' or content == 'img2text':
                command = self.COMMANDS.IMG_TO_TEXT
            elif command == u'退出' or content == 'exit':
                command = self.COMMANDS.EXIT
        elif msg.type == 'image':
            command = self.COMMANDS.MENU

        # 记录下来当前的命令.
        self.cache.set(msg.source, command)
        logging.debug('God command:%s from msg:%s', command, msg)
        return command

    def menus(self, msg):
        """菜单,当用户发送图片来的时候默认激发此菜单"""
        resp = ''
        if msg.type == 'image':
            self.cache.set(msg.source + '_img_url', msg.image)
            resp = u'收到一张图，'
        menus = [
            u'* 颜龄 : 查看您的年龄',
            u'* 看图说话 : AI识别图的内容',
            u'* 大头贴 : 选择数字(1-30)的一种大头贴特效'
            u'* 滤镜 : 为您的照片增加一层滤镜',
            u'* 人脸融合 : 古装/科幻等特效(特效支持1-50的范围)',
            u'* 退出 : 退出上下文',
        ]
        # 菜单功能正常结束.
        self.cache.delete(msg.source)
        return u'%s你是要我做什么呢?\n\n%s' % (resp, '\n'.join(menus))

    def response(self, request):
        msg = parse_message(request.data)
        for plugin in self.plugins:
            if plugin.match(msg, bot=self):
                logging.debug('%s matched the msg: %s', plugin.__name__, msg)
                resp = plugin.response(msg, bot=self)
                if resp:
                    return resp
                logging.debug('消息没有返回,跳过用此插件(%s)处理', plugin.__name__)

        command = self.parse_command(msg)
        reply = getattr(self, command, self.nlp_chat)(msg)
        return self.create_resp(reply, msg)


if __name__ == '__main__':
    import plugins as p

    print 'loaded plugins:', load_plugins(p)
