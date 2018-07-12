# -*- coding:utf-8 -*-

import re
import base64
import urllib
import importlib
import pkgutil
import logging
from enum import Enum
from cStringIO import StringIO
from collections import namedtuple, OrderedDict

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


CommandItem = namedtuple('CommandItem', ['re', 'method', 'desc'])


class LogicException(Exception):
    pass


class AI(object):
    command_type = Enum('Command', 'CHAT AGE STICKER MERGE DECORATION COSMETIC FILTER VISION MENUS EXIT')

    def __init__(self, api_id, api_key, plugins):
        self.plugins = plugins
        self.ai = AiPlat(api_id, api_key)
        self._bootstrap_plugins()
        self.cache = FileSystemCache('/tmp/wechat-bot-cache')
        self.available_cmds = OrderedDict()
        self.client = None
        self.register_default_cmd()

    def register_default_cmd(self):

        # 聊天功能
        self.register_cmd(self.command_type.CHAT,
                          CommandItem(re='(?i)^chat$', method=(self, 'nlp_chat'), desc='* Chat : 聊天/默认行为'))

        # 颜龄功能
        self.register_cmd(self.command_type.AGE,
                          CommandItem(re='(?i)^a(ge)?$', method=(self, 'face_age'), desc='* A(age) : 查看颜龄'))

        # 大头贴功能
        self.register_cmd(self.command_type.STICKER,
                          CommandItem(re='(?i)^s(ticker)?$', method=(self, 'face_sticker'),
                                      desc='* S(sticker) : 大头贴'))

        # 人脸融合
        self.register_cmd(self.command_type.MERGE,
                          CommandItem(re='(?i)^m(erge)?$', method=(self, 'face_merge'), desc='* M(merge) : 人脸融合'))

        # 人脸变妆
        self.register_cmd(self.command_type.DECORATION,
                          CommandItem(re='(?i)^d(ecoration)?$', method=(self, 'face_decoration'),
                                      desc='* D(decoration) : 人脸变妆'))
        # 人脸美妆
        self.register_cmd(self.command_type.COSMETIC,
                          CommandItem(re='(?i)^c(osmetic)?$', method=(self, 'face_cosmetic'),

                                      desc='* C(cosmetic) : 人脸美妆'))
        # 滤镜
        self.register_cmd(self.command_type.FILTER,
                          CommandItem(re='(?i)^f(ilter)?$', method=(self, 'image_filter'),
                                      desc='* F(filter) : 图像滤镜'))
        # 看图说话
        self.register_cmd(self.command_type.VISION,
                          CommandItem(re='(?i)^v(ision)?$',
                                      method=(self, 'image_to_text'),
                                      desc='* V(vision) : 看图说话'))
        # 菜单
        self.register_cmd(self.command_type.MENUS,
                          CommandItem(re='(?i)^menu$',
                                      method=(self, 'menus'),
                                      desc='* Menu : 显示此菜单'))
        # 退出.
        self.register_cmd(self.command_type.EXIT,
                          CommandItem(re=ur'(?iu)^(e(xit)?|\u9000\u51fa)$',
                                      method=(self, 'exit'),
                                      desc='* E(exit) : 退出上下文'))

    def register_cmd(self, cmd_type, cmd):
        if hasattr(cmd_type, 'name'):
            cmd_type = cmd_type.name
        self.available_cmds[cmd_type] = cmd

    def unregister_cmd(self, cmd_type):
        if cmd_type in self.available_cmds:
            del self.available_cmds[cmd_type]

    def get_cmd(self, cmd_type, default=None):
        return self.available_cmds.get(cmd_type, default)

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
        self.cache.delete(msg.source)
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
            reply = create_reply(u'%s, 重新发送一张图试试吧!' % resp['msg'], msg)
        return reply

    def reply_help_img(self, msg, file):
        mid = self._media_upload(media_file=file)
        if not mid:
            return u'请回复你要的特效编号:1-30'
        return ImageReply(
            media_id=mid,
            message=msg
        )

    def face_age(self, msg):
        img = self.get_current_img(msg)
        if not img:
            return u'请先发送一张有人脸的图片哦'
        resp = self.ai.ptu_faceage(img)
        return self.image_resp(msg, resp)

    def face_sticker(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/sticker.png', 'rb'))
        img = self.get_current_img(msg)
        if not img:
            return u'请先发送一张有人脸的图片哦'
        resp = self.ai.ptu_facesticker(img, msg.content)
        return self.image_resp(msg, resp)

    def face_merge(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/merge.png', 'rb'))
        img = self.get_current_img(msg)
        if not img:
            return u'请先发送一张有人脸的图片哦'
        resp = self.ai.ptu_facemerge(img, msg.content)
        return self.image_resp(msg, resp)

    def face_decoration(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/decoration.png', 'rb'))
        img = self.get_current_img(msg)
        if not img:
            return u'请先发送一张有人脸的图片哦'
        resp = self.ai.ptu_facedecoration(img, msg.content)
        return self.image_resp(msg, resp)

    def face_cosmetic(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/cosmetic.png', 'rb'))
        img = self.get_current_img(msg)
        if not img:
            return u'请先发送一张有人脸的图片哦'
        resp = self.ai.ptu_facecosmetic(img, msg.content)
        return self.image_resp(msg, resp)

    def image_to_text(self, msg):
        img = self.get_current_img(msg)
        if not img:
            return u'请先发送图片给我哦'
        resp = self.ai.vision_image(img, msg.source)
        text = resp['data']['text'] if resp['ret'] == 0 else resp['msg']
        self.cache.delete(msg.source)
        return text

    def image_filter(self, msg):
        if msg.type != 'text' or not msg.content.isdigit():
            return self.reply_help_img(msg, file=open('data/filter.png', 'rb'))
        img = self.get_current_img(msg)
        if not img:
            return u'请先发送图片给我哦'
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

        # 优先检查是否需要退出
        exit_cmd = self.available_cmds.get(self.command_type.EXIT.name)
        if not exit_cmd:
            raise LogicException('Command: %s is required!' % self.command_type.EXIT)

        if msg.type == 'text' and re.match(exit_cmd.re, msg.content):
            return exit_cmd

        cmd_type_name = self.cache.get(msg.source)
        if cmd_type_name:
            logging.debug('God command:%s from history(cached)', cmd_type_name)
            return self.available_cmds[cmd_type_name]

        cmd_type_name = self.command_type.CHAT.name
        if msg.type == 'text':
            content = msg.content
            for name, cmd in self.available_cmds.iteritems():
                if re.match(cmd.re, content):
                    cmd_type_name = name
                    break
        elif msg.type == 'image':
            cmd_type_name = self.command_type.MENUS.name

        # 记录下来当前的命令名字
        self.cache.set(msg.source, cmd_type_name)
        logging.debug('Got command:%s from msg', cmd_type_name)
        return self.available_cmds.get(cmd_type_name)

    def menus(self, msg):
        """菜单,当用户发送图片来的时候默认激发此菜单"""
        resp = ''
        if msg.type == 'image':
            self.cache.set(msg.source + '_img_url', msg.image)
            resp = u'收到一张图，'
        # 菜单功能正常结束.
        self.cache.delete(msg.source)
        return u'%s你是要我做什么呢? 请输入菜单对应的首字母/单词\n\n%s' % (resp,
                                                      '\n'.join(
                                                          cmd.desc for cmd in self.available_cmds.values()).decode(
                                                          'utf-8'))

    def response(self, request):
        msg = parse_message(request.data)
        for plugin in self.plugins:
            if plugin.match(msg, bot=self):
                logging.debug('%s matched the msg: %s', plugin.__name__, msg)
                resp = plugin.response(msg, bot=self)
                if resp:
                    return self.create_resp(resp, msg)
                logging.debug('消息没有返回,跳过用此插件(%s)处理', plugin.__name__)

        command = self.parse_command(msg)
        if not command:
            logging.error('Unsupported Command: %s, Try to use default command(Chat)', command)
            command = self.nlp_chat
        elif callable(command.method):
            command = command.method
        else:
            command = getattr(*command.method)

        reply = command(msg)
        return self.create_resp(reply, msg)


if __name__ == '__main__':
    FakeMsg = namedtuple('FakeMsg', ['content', 'type', 'source'])
    msg = FakeMsg(content=u'test_callback', type='text', source='shellvon')
    ai = AI('', '', [])

    import sys

    this_md = sys.modules[__name__]


    def hello_world(msg):
        return 'Got msg', msg


    ai.register_cmd('test_callback', CommandItem(desc='Test Register Cmd', re='(?iu)test_callback', method=(
        this_md, 'hello_world', lambda x: sys.stdout.write('Hello ' + str(x)))))  # 第三个参数是可选的默认函数

    cmd = ai.parse_command(msg)
    if cmd:
        print 'Got Cmd:', cmd
        callback = getattr(*ai.parse_command(msg).method)
        print callback(msg)
    else:
        print 'No available command to process it.'
