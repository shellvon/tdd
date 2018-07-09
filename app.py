# -*- coding:utf-8 -*-

import logging

from flask import Flask, abort, request
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException, WeChatClientException
from wechatpy.client import WeChatClient

import plugins
import setting
from bot import AI, load_plugins

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S')


def create_app(config_file):
    app = Flask(__name__)
    app.config.from_object(config_file)
    return app


app = create_app('setting')

bot = AI(setting.TENCENT_AI_APP_ID, setting.TENCENT_AI_APP_KEY, load_plugins(plugins))

wechat_client = WeChatClient(setting.WECHAT_APP_ID, setting.WECHAT_APP_SECRET)
# WTF.
bot.wechat_client = wechat_client

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
    app.run(host=app.config.get('HOST'))


if __name__ == '__main__':
    main()
