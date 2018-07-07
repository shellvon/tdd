# -*- coding:utf-8 -*-

import logging

from flask import Flask, abort, request
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import (
    InvalidSignatureException
)

import plugins
from bot import AI, load_plugins
from setting import (
    WECHAT_TOKEN,
    TENCENT_AI_APP_ID,
    TENCENT_AI_APP_KEY
)


def create_app(config_file):
    app = Flask(__name__)
    app.config.from_object(config_file)
    return app


app = create_app('setting')
bot = AI(TENCENT_AI_APP_ID, TENCENT_AI_APP_KEY, load_plugins(plugins))


@app.route('/wechat-bot', methods=['GET', 'POST'])
def wechat():
    sign = request.args.get('signature', '')
    ts = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    encrypt_type = request.args.get('encrypt_type', 'raw')
    try:
        check_signature(WECHAT_TOKEN, sign, ts, nonce)
    except InvalidSignatureException:
        return abort(403)
    if request.method == 'GET':
        echo_str = request.args.get('echostr', '')
        return echo_str
    # POST request.
    if encrypt_type != 'raw':
        return 'Sorry, I Don\'t Understand'
    msg = parse_message(request.data)
    resp = bot.response(msg)
    if not resp:
        return create_reply('不好意思,目前我还无法处理您的消息,试试其他的吧.', msg, render=True)
    if isinstance(resp, (str, unicode, tuple, list)):
        return create_reply(resp, msg, render=True)
    return create_reply('我晕了～', msg, render=True)


def main():
    logging.basicConfig(level=logging.DEBUG)
    app.run(host=app.config.get('HOST'))


if __name__ == '__main__':
    main()
