"""
Author: iota
Create: 2023.12.21 17:56
Project: YuanShenTool
Path: src/modules/ocr.py
IDE: PyCharm
Description: 实现本地及云端OCR类
"""
import time
from abc import ABC, abstractmethod

import requests

from src.modules.base import config, logger
from src.utils.cyber import *

ocr_config = config['ocr_config']
DEBUG_MODE = config['debug_mode']
SCREENSHOTS_DIR = 'debug/screenshots/'

if DEBUG_MODE:
    import os
    import cv2
    import numpy as np

    if os.path.exists(SCREENSHOTS_DIR):
        for fi in os.listdir(SCREENSHOTS_DIR):
            os.remove(SCREENSHOTS_DIR + fi)
    else:
        os.mkdir(SCREENSHOTS_DIR)


class BaseOCR(ABC):
    def __init__(self):
        self.__count = 0

    @abstractmethod
    def scan_image(self,
                   image_bytes: bytes,
                   ret_detail: bool,
                   compression_ratio=1) -> list[list[tuple[int] | str | float]] | list[str]:
        """识别图像中的文本

        为统一OCR识别图片方法的输入输出格式，新建OCR类需按照规则重写本方法。

        :param image_bytes: 图片字节流
        :param ret_detail: 是否返回更多细节
        :param compression_ratio: 压缩图片比例
        :return: 当ret_detail为真，每项按照 [矩形顶点位置, 识别文字, 可信度] 的格式放入列表中再返回；
                 否则，直接将识别到的文字放入一个列表中返回。
        """

    def record_detected_image(self, image_bytes, detection, detail):
        """记录识别结果并附在图片上

        :param image_bytes: 图片字节流
        :param detection: 识别结果
        :param detail: 结果是否存在位置等细节
        :return:
        """
        image_array = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), flags=cv2.IMREAD_UNCHANGED)

        if detail:
            for item in detection:
                top_left = item[0][0]
                bottom_right = item[0][2]
                text = '%s (%.3f)' % (item[1], item[2])
                image_array = cv2.rectangle(image_array, pt1=top_left, pt2=bottom_right, color=(0, 255, 0), thickness=1)
                image_array = cv2.putText(image_array, text=text, org=top_left,
                                          fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(0, 0, 255),
                                          thickness=1, lineType=cv2.LINE_AA)
        else:
            left_top = [1, 20]
            for text in detection:
                image_array = cv2.putText(image_array, text=text, org=left_top,
                                          fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(0, 0, 255),
                                          thickness=1, lineType=cv2.LINE_AA)
                left_top[1] += 20

        img_path = '%s/%s-%03d.png' % (SCREENSHOTS_DIR, time.strftime('%H%M%S'), self.__count)
        cv2.imwrite(img_path, image_array)
        logger.debug(f'图像[{img_path}]识别结果: {detection}')
        self.__count += 1


class EasyOCR(BaseOCR):
    def __init__(self):
        import easyocr

        super().__init__()

        local_ocr_config = ocr_config['local']
        self.reader = easyocr.Reader(local_ocr_config['lang_list'], gpu=local_ocr_config['use_gpu'])

    def scan_image(self, image_bytes, ret_detail, compression_ratio=1):
        detection = self.reader.readtext(image_bytes, detail=ret_detail, mag_ratio=compression_ratio,
                                         text_threshold=0.75, link_threshold=0.05)
        if DEBUG_MODE:
            self.record_detected_image(image_bytes, detection, ret_detail)
        return detection


class BaiduOCR(BaseOCR):
    def __init__(self):
        super().__init__()

        baidu_ocr_config = ocr_config['baidu']
        self.API_KEY = baidu_ocr_config['api_key']
        self.SECRET_KEY = baidu_ocr_config['secret_key']

        self.BASE_URL = 'https://aip.baidubce.com'
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        self.access_token = None
        self.refresh_access_token()
        if self.access_token is None:
            raise ValueError('获取接口令牌失败')

        self.api_version = 'general'

    def refresh_access_token(self):
        api = self.BASE_URL + '/oauth/2.0/token'
        url = api + f'?grant_type=client_credentials&client_id={self.API_KEY}&client_secret={self.SECRET_KEY}'
        logger.debug('==> POST %s' % url)
        response = requests.post(url)
        self.access_token = response.json().get('access_token')
        logger.debug('<== %s %s %s..' % (response.status_code, api, response.text[:100]))

    def send_image_to_webapi(self, image_base64, locate_text=True):
        api = self.BASE_URL + '/rest/2.0/ocr/v1/' + (self.api_version if locate_text else self.api_version + '_basic')
        url = api + f'?access_token={self.access_token}'
        payload = 'vertexes_location={1}&probability={1}&image={0}'.format(urlencoded(image_base64),
                                                                           'true' if locate_text else 'false')
        logger.debug('==> POST %s %s..' % (url, payload[:100]))
        response = requests.post(url, headers=self.headers, data=payload)
        logger.debug('<== %s %s %s..' % (response.status_code, api, response.text[:100]))
        return response.json()

    def scan_image(self, image_bytes, ret_detail, compression_ratio=1):
        if self.access_token is None:
            logger.error('token不能为空')
            return None
        if not image_bytes:
            logger.error('image不能为空')
            return None

        image_base64 = bytes_to_base64str(image_bytes)
        result = self.send_image_to_webapi(image_base64, locate_text=ret_detail)
        detection = []
        try:
            for item in result['words_result']:
                text = item['words']
                if ret_detail:
                    rect = [(_['x'], _['y']) for _ in item['vertexes_location']]
                    prob = item['probability']['average']
                    detection.append([rect, text, prob])
                else:
                    detection.append(text)
        except KeyError as ke:
            self.api_version = 'accurate'
            raise UserWarning(f'接口返回数据错误，请重试或检查：{ke}')
        if DEBUG_MODE:
            self.record_detected_image(image_bytes, detection, ret_detail)
        return detection


def get_ocr(ocr_name):
    """根据OCR名称去实例化一个OCR实现类

    :param ocr_name: OCR名称
    :return: OCR实例化的对象
    """
    ocr_platforms = {
        'local': EasyOCR,
        'baidu': BaiduOCR
    }
    ocr_class = ocr_platforms.get(ocr_name)
    if ocr_class:
        logger.info(f'{ocr_class=}')
        return ocr_class()
    raise ValueError('选择的OCR平台不存在：%s\n可选：%s' % (ocr_name, list(ocr_platforms)))


if __name__ == '__main__':
    logger.info('start..')
    obj = get_ocr('local')

    with open('debug/screenshot.png', 'rb') as fp:
        start = time.time()
        res = obj.scan_image(fp.read(), ret_detail=True)
        logger.info(time.time() - start)
        logger.info(res)
