"""
Author: iota
Create: 2024.1.27 22:45
Project: YuanShenTool
Path: src/utils/img.py
IDE: PyCharm
Description: 图像处理有关方法
"""

import time

import numpy as np
from PIL import Image

from src.modules.ocr import DEBUG_MODE, SCREENSHOTS_DIR


class Debug:
    __count = 0

    @classmethod
    def record(cls, image, number):
        image_path = '%s/%s-%03d_img_%d.png' % (SCREENSHOTS_DIR, time.strftime('%H%M%S'), cls.__count, number)
        with open(image_path, 'wb') as image_file:
            image.save(image_file)
        cls.__count += 1


def count_pixels_of_color(image: Image.Image, target_color: tuple, tolerance=0):
    """计算图片中给定颜色的像素数量

    相当于计算图片中某种颜色区域的面积

    :param image: 图片对象
    :param target_color: 目标颜色
    :param tolerance: 容差
    :return:
    """
    image_array = np.array(image)
    target_color_array = np.array(target_color)

    if tolerance == 0:
        diff_array = image_array == target_color_array
    else:
        diff_array = np.abs(image_array - target_color_array) <= tolerance
    matching_pixels = np.all(diff_array, axis=-1)
    pixels_number = np.sum(matching_pixels)

    if DEBUG_MODE:
        image_array[matching_pixels] = [0, 0, 0]
        result_image = Image.fromarray(image_array)
        Debug.record(result_image, pixels_number)
    return pixels_number


if __name__ == '__main__':
    with open('debug/testdata/test1.png', 'rb') as fp:
        img = Image.open(fp)
        start = time.perf_counter()
        num = count_pixels_of_color(img, (255, 192, 64), tolerance=10)
        print(time.perf_counter() - start)
    print(f'匹配像素数量：{num}')
