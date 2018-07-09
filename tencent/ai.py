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
        print app_id, app_key
    @staticmethod
    def code_to_msg(code):
        """
        将错误代码映射成中文.
        https://ai.qq.com/doc/returncode.shtml

        # Javascript Code:
        s = $('body > div.layout.main-cont > div.main.markdown-body > table:nth-child(18) > tbody > tr > td:nth-child(-n+2)'
        json = {}
        for(var i=0,l=s.length; i < l; i+=2) {json[s[i].innerText]  = s[i+1].innerText;}
        JSON.stringify(json, null, 4)
        """

        code_maps = {
            "4096": "参数非法",
            "12289": "应用不存在",
            "12801": "素材不存在",
            "12802": "素材ID与应用ID不匹配",
            "16385": "缺少app_id参数",
            "16386": "缺少time_stamp参数",
            "16387": "缺少nonce_str参数",
            "16388": "请求签名无效",
            "16389": "缺失API权限",
            "16390": "time_stamp参数无效",
            "16391": "同义词识别结果为空",
            "16392": "专有名词识别结果为空",
            "16393": "意图识别结果为空",
            "16394": "闲聊返回结果为空",
            "16396": "图片格式非法",
            "16397": "图片体积过大",
            "16402": "图片没有人脸",
            "16403": "相似度错误",
            "16404": "人脸检测失败",
            "16405": "图片解码失败",
            "16406": "特征处理失败",
            "16407": "提取轮廓错误",
            "16408": "提取性别错误",
            "16409": "提取表情错误",
            "16410": "提取年龄错误",
            "16411": "提取姿态错误",
            "16412": "提取眼镜错误",
            "16413": "提取魅力值错误",
            "16414": "语音合成失败",
            "16415": "图片为空",
            "16416": "个体已存在",
            "16417": "个体不存在",
            "16418": "人脸不存在",
            "16419": "分组不存在",
            "16420": "分组列表不存在",
            "16421": "人脸个数超过限制",
            "16422": "个体个数超过限制",
            "16423": "组个数超过限制",
            "16424": "对个体添加了几乎相同的人脸",
            "16425": "无效的图片格式",
            "16426": "图片模糊度检测失败",
            "16427": "美食图片检测失败",
            "16428": "提取图像指纹失败",
            "16429": "图像特征比对失败",
            "16430": "OCR照片为空",
            "16431": "OCR识别失败",
            "16432": "输入图片不是身份证",
            "16433": "名片无足够文本",
            "16434": "名片文本行倾斜角度太大",
            "16435": "名片模糊",
            "16436": "名片姓名识别失败",
            "16437": "名片电话识别失败",
            "16438": "图像为非名片图像",
            "16439": "检测或者识别失败",
            "16440": "未检测到身份证",
            "16441": "请使用第二代身份证件进行扫描",
            "16442": "不是身份证正面照片",
            "16443": "不是身份证反面照片",
            "16444": "证件图片模糊",
            "16445": "请避开灯光直射在证件表面",
            "16446": "行驾驶证OCR识别失败",
            "16447": "通用OCR识别失败",
            "16448": "银行卡OCR预处理错误",
            "16449": "银行卡OCR识别失败",
            "16450": "营业执照OCR预处理失败",
            "16451": "营业执照OCR识别失败",
            "16452": "意图识别超时",
            "16453": "闲聊处理超时",
            "16454": "语音识别解码失败",
            "16455": "语音过长或空",
            "16456": "翻译引擎失败",
            "16457": "不支持的翻译类型",
            "16460": "输入图片与识别场景不匹配",
            "16461": "识别结果为空"
        }

        return code_maps.get(str(code), '未知错误代码: %s' % code)

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

    def _parse_resp(self, resp):
        code = resp['ret']
        if code != 0:
            resp['msg'] = self.code_to_msg(code)
        return resp

    def invoke(self, data=None):
        data.update(self._common_params)
        data['sign'] = self.checksum(data)
        url = '%s%s' % (BASE_URI, self.end_point)
        resp = self.req.post(url, data=data).json()
        logging.debug('request:<%s>, resp:<%s>', self.end_point, resp)
        return self._parse_resp(resp)

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
        self.end_point = '/ptu/ptu_faceage'
        return self._ptu(image)

    def ptu_facesticker(self, image, sticker=1):
        self.end_point = '/ptu/ptu_facesticker'
        return self._ptu(image, sticker=sticker)


def main():
    api = AiPlat('1107021444', 'Zs4iYs0ghKRh0nZ0')


    import json

    print json.dumps(api.nlp_chat('user_a', '天气'), ensure_ascii=False, indent=4)
    print json.dumps(api.nlp_chat('user_a', '成都'), ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
