# -*- coding:utf-8 -*-

import time
import uuid
import base64
import urllib
import hashlib
import requests
import logging

BASE_URI = 'https://api.ai.qq.com/fcgi-bin'


def safe_quote(value, safe=''):
    if isinstance(value, unicode):
        value = value.encode('utf-8')
    elif not isinstance(value, str):
        value = str(value)
    return urllib.quote_plus(value, safe=safe)


class AiPlat(object):

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.req = requests.Session()
        self.end_point = ''

    def checksum(self, payloads):
        sorted_dict = sorted(payloads.items(), key=lambda item: item[0], reverse=False)

        plain_text = ''
        for (key, value) in sorted_dict:
            if key == 'app_key':
                continue
            plain_text += '%s=%s&' % (key, safe_quote(value))
        plain_text += 'app_key=%s' % self.app_key
        return hashlib.md5(plain_text).hexdigest().upper()

    @property
    def nonce(self):
        return uuid.uuid4().hex

    @property
    def curtime(self):
        return str(int(time.time()))

    def invoke(self, data=None):
        data.update(self._common_params)
        data['sign'] = self.checksum(data)
        url = '%s%s' % (BASE_URI, self.end_point)
        resp = self.req.post(url, data=data).json()
        logging.debug('request:<%s>, resp:<%s>', self.end_point, resp)
        return resp

    @property
    def _common_params(self):
        return {
            'app_id': self.app_id,
            'time_stamp': self.curtime,
            'nonce_str': self.nonce,
        }

    def nlp_chat(self, session, question):
        self.end_point = '/nlp/nlp_textchat'
        payloads = {
            'session': session,
            'question': question
        }
        return self.invoke(data=payloads)

    def nlp_trans(self, text, type=0):
        '''
        type: string 翻译类型 https://ai.qq.com/doc/nlptrans.shtml#5-%E7%BF%BB%E8%AF%91%E7%B1%BB%E5%9E%8B%E5%AE%9A%E4%B9%89
        '''
        self.end_point = '/nlp/nlp_texttranslate'
        payloads = {
            'type': type,
            'text': text
        }
        return self.invoke(data=payloads)

    def _ptu(self, image, **kwargs):
        if isinstance(image, (str, bytes, unicode)):
            b64str = base64.b64encode(image)
        elif isinstance(image, file):
            b64str = base64.b64encode(image.read())
        else:
            b64str = str(image)
        payloads = {
            'image': b64str
        }
        if kwargs:
            payloads.update(kwargs)
        return self.invoke(payloads)

    def vision_image(self, image, session_id):
        self.end_point = '/vision/vision_imgtotext'
        return self._ptu(image, session_id=session_id)

    def ptu_facecosmetic(self, image, cosmetic=1):
        '''https://ai.qq.com/doc/facecosmetic.shtml'''
        return self._ptu(image, cosmetic=cosmetic)

    def ptu_facedecoration(self, image, decoration=1):
        self.end_point = '/ptu/ptu_facedecoration'
        return self._ptu(image, decoration=decoration)

    def ptu_imagefilter(self, image, filter=1):
        self.end_point = '/ptu/ptu_imgfilter'
        return self._ptu(image, filter=filter)

    def ptu_facemerge(self, image, model=1):
        '''https://ai.qq.com/doc/facemerge.shtml'''
        self.end_point = '/ptu/ptu_facemerge'
        return self._ptu(image, model=model)

    def ptu_faceage(self, image):
        return self._ptu(image)


def main():
    api = AiPlat('xxxx', 'xxxx')
    print api.nlp_chat('hello', '你是谁 ?')


if __name__ == '__main__':
    main()
