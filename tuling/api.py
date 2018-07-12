# -*- coding:utf-8 -*-

import requests
import logging


class API(object):
    """
    图灵API V2版本 https://www.kancloud.cn/turing/web_api/522992
    """
    BASE_URI = 'http://openapi.tuling123.com/openapi/api/v2'

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.req = requests.Session()
        self.req.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        })
        self.codes = {
            "0": "上传成功",
            "4000": "请求参数格式错误",
            "4001": "加密方式错误",
            "4002": "无功能权限",
            "4003": "该apikey没有可用请求次数",
            "4005": "无功能权限",
            "4007": "apikey不合法",
            "4100": "userid获取失败",
            "4200": "上传格式错误",
            "4300": "批量操作超过限制",
            "4400": "没有上传合法userid",
            "4500": "userid申请个数超过限制",
            "4600": "输入内容为空",
            "4602": "输入文本内容超长(上限150)",
            "5000": "无解析结果",
            "6000": "暂不支持该功能",
            "7002": "上传信息失败",
            "8008": "服务器错误"
        }

    def request(self, user_info, req_type=0, text=None, image=None, media=None, self_info=None):
        payloads = {
            'reqType': req_type,
            'perception': {}
        }
        if isinstance(user_info, dict):
            user_info['apiKey'] = self.api_key
            payloads['userInfo'] = user_info
        else:
            payloads['userInfo'] = {'userId': user_info, 'apiKey': self.api_key}
        if not any([text, image, media]):
            raise ValueError('text/image/media at least one!')
        if text:
            payloads['perception']['inputText'] = {'text': text}
        if image:
            payloads['perception']['inputImage'] = {'url': image}
        if media:
            payloads['perception']['inputMedia'] = {'url': media}
        if self_info:
            if not isinstance(self_info, dict):
                raise ValueError('self_info must be a dict')
            location = self_info.get('location', self_info)
            if not isinstance(location, dict):
                raise ValueError('location must be a dict')
            if 'city' not in location:
                raise ValueError('location.city is required')
            payloads['perception']['selfInfo'] = {'location': location}
        resp = self.req.post(self.BASE_URI, json=payloads).json()

        return self._process_resp(resp)

    def _process_resp(self, resp):
        code = self.codes.get(str(resp['intent']['code']))
        if code:
            logging.error('请求图灵API失败: %s', code)
            return {'text': code}  # 以文本消息返回.

        result = {}
        for r in resp['results']:
            result.setdefault(r['groupType'], {}).update(**r['values'])

        result = result.values()
        if not result:
            return
        if len(result) > 1:
            logging.error('同一API请求出现多个Group')
        import json
        print json.dumps(result[0], ensure_ascii=False, indent=4)
        return result[0]


if __name__ == '__main__':
    bot = API('')
    resp = bot.request('testuid', text=u'帮我搜一张好看的狗图')
