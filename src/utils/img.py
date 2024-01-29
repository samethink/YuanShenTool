"""
Author: iota
Create: 2024.1.27 22:45
Project: YuanShenTool
Path: src/utils/img.py
IDE: PyCharm
Description: 图像处理有关方法
"""
import io

import numpy as np
from PIL import Image


def count_pixels_of_color(image_bytes, target_color, tolerance=0, _show_result=False):
    """计算图片中给定颜色的像素数量

    相当于计算图片中某种颜色区域的面积

    :param image_bytes: 图片字节流
    :param target_color: 目标颜色
    :param tolerance: 容差
    :param _show_result: 展示匹配效果
    :return:
    """
    image_array = np.array(Image.open(io.BytesIO(image_bytes)))
    target_color_array = np.array(target_color)
    matching_pixels = np.all(np.abs(image_array - target_color_array) <= tolerance, axis=-1)
    if _show_result:
        image_array[matching_pixels] = [0, 0, 0]
        result_image = Image.fromarray(image_array)
        result_image.show()
    return np.sum(matching_pixels)


if __name__ == '__main__':
    import time

    image_path = 'debug/testdata/test1.png'
    file = open(image_path, 'rb')
    image = file.read()
    start = time.perf_counter()
    pixel_count = count_pixels_of_color(image, (255, 192, 63), tolerance=50, _show_result=False)
    print(time.perf_counter() - start)
    file.close()
    print(f'匹配像素数量：{pixel_count}')
