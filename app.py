# -*- coding:utf-8 -*-

import logging

from flask import Flask, abort, request
from wechatpy import create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.client import WeChatClient

import plugins
import setting
from bot import AI, load_plugins, CommandItem

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S')


def create_app(config_file):
    app = Flask(__name__)
    app.config.from_object(config_file)
    return app


app = create_app('setting')

bot = AI(setting.TENCENT_AI_APP_ID, setting.TENCENT_AI_APP_KEY, load_plugins(plugins))


def tuling_bot(bot):
    from hashlib import md5
    from tuling import API
    http = API(setting.TULING_API_KEY)

    def tuling_chat_command(message):
        bot.cache.set(message.source, 'TDD')  # 别过期.
        user_id = md5(message.source).hexdigest()
        if message.type != 'text':
            return u'仅支持纯文字聊天'

        if message.content.lower() == 't' or message.content.lower() == 'tdd':
            return u'Hello,我是淘逗逗的姐姐^_^, 谢谢你把我召唤出来'

        resp = http.request(user_id, text=message.content)
        if 'news' in resp:
            # 新闻
            articles = [{'title': el['name'] + el['info'], 'description': '%s : %s' % (resp['text'], el['name']),
                         'image': el['icon'], 'url': el['detailurl']} for el in resp['news'][:3]]
            return create_reply(articles, message)
        elif 'url' in resp:
            # 链接类消息(航班/路线/百科等)
            return create_reply(u'{text}:\n{url}'.format(**resp), message)
        elif 'image' in resp:
            logging.error('Image Repsonse....')
        elif 'video' in resp or 'voice' in resp:
            logging.error('Media Repsonse....')
        else:
            logging.error('Unsupported Repsonse....')

        return create_reply(resp['text'], message)

    return tuling_chat_command


@app.route('/wechat-bot', methods=['GET', 'POST'])
def wechat():
    sign = request.args.get('signature', '')
    ts = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    encrypt_type = request.args.get('encrypt_type', 'raw')
    try:
        check_signature(setting.WECHAT_TOKEN, sign, ts, nonce)
    except InvalidSignatureException:
        return abort(403)
    if request.method == 'GET':
        echo_str = request.args.get('echostr', '')
        return echo_str
    # POST request.
    if encrypt_type != 'raw':
        return 'Sorry, I Don\'t Understand'
    return bot.response(request)


def main():
    wechat_client = WeChatClient(setting.WECHAT_APP_ID, setting.WECHAT_APP_SECRET)
    # Dirty hack
    bot.wechat_client = wechat_client
    # 注册一个新的聊天机器人
    bot.register_cmd('TDD', CommandItem(desc='* T(dd): 使用淘逗逗2号机器人聊天',
                                        re='(?i)^t(dd)?$',
                                        method=tuling_bot(bot)))
    app.run(host=app.config.get('HOST'))


if __name__ == '__main__':
    main()
