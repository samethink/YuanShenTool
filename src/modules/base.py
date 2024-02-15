"""
Author: iota
Create: 2023.12.14 15:17
Project: YuanShenTool
Path: src/modules/base.py
IDE: PyCharm
Description: 定义窗口基础动作
"""
import ctypes
import time

import mss
import mss.tools
from PIL import Image

from src.utils.support import logger, pub_config


class Automize:
    def __init__(self, window_title, window_classname=None, _admin_permission_required=False):
        """初始化窗口动作对象

        :param window_title: 匹配窗口标题
        :param window_classname: 匹配窗口类名
        :param _admin_permission_required: 操作窗口是否需要管理员权限
        """
        if _admin_permission_required and not ctypes.windll.shell32.IsUserAnAdmin():
            raise PermissionError('程序未获得管理员权限')

        self.window_title = window_title
        self.window_classname = window_classname
        logger.info('目标窗口标题=%s, 类名=%s' % (self.window_title, self.window_classname))

        self.window_handle = None
        self.refresh_window_handle()

        self.ACTION_DELAY = pub_config['action_delay']

        # 标准分辨率：1920x1080，代码中的 x/y 坐标数值是基于该分辨率下的
        self.SCREEN_SIZE = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
        logger.info('屏幕尺寸：%dx%d' % self.SCREEN_SIZE)
        self.__x_ratio = self.SCREEN_SIZE[0] / 1920
        self.__y_ratio = self.SCREEN_SIZE[1] / 1080

    def refresh_window_handle(self):
        self.window_handle = ctypes.windll.user32.FindWindow(self.window_classname, self.window_title)
        logger.info(f'句柄={self.window_handle}')

    def activate_window(self) -> bool:
        self.refresh_window_handle()
        if self.window_handle:
            ctypes.windll.user32.ShowWindow(self.window_handle, 9)
            ctypes.windll.user32.SetForegroundWindow(self.window_handle)
            self.waiting(1)
            return True
        return False

    def get_window_position(self) -> tuple | None:
        return ctypes.windll.user32.GetWindowRect(self.window_handle)

    def is_window_on_top(self) -> bool:
        return self.window_handle == ctypes.windll.user32.GetForegroundWindow()

    def move_to(self, x: int, y: int):
        ctypes.windll.user32.SetCursorPos((x * self.__x_ratio, y * self.__y_ratio))

    def click(self, x: int, y: int):
        x *= self.__x_ratio
        y *= self.__y_ratio
        ctypes.windll.user32.SetCursorPos((x, y))
        ctypes.windll.user32.mouse_event(2, x, y, 0, 0)
        ctypes.windll.user32.mouse_event(4, x, y, 0, 0)
        self.waiting(1)

    def scroll(self, count: int, duration: float = None):
        if duration is None:
            duration = self.ACTION_DELAY
        symbol = 1 if count > 0 else -1
        count = abs(count)
        delay = duration / count
        for _ in range(count):
            ctypes.windll.user32.mouse_event(8, 0, 0, symbol)
            time.sleep(delay)
        self.waiting(1)

    def waiting(self, multiple: int | float = 1):
        time.sleep(self.ACTION_DELAY * multiple)

    mss_sct = mss.mss()

    def __screenshot(self, x1, y1, x2, y2):
        return self.mss_sct.grab((x1 * self.__x_ratio, y1 * self.__y_ratio,
                                  x2 * self.__x_ratio, y2 * self.__y_ratio))

    def take_screenshot(self, x1, y1, x2, y2) -> bytes:
        screenshot = self.__screenshot(x1, y1, x2, y2)
        return mss.tools.to_png(screenshot.rgb, screenshot.size)

    def take_screenshot_as_image(self, x1, y1, x2, y2) -> Image.Image:
        screenshot = self.__screenshot(x1, y1, x2, y2)
        return Image.frombytes('RGB', screenshot.size, screenshot.rgb)


if __name__ == '__main__':
    logger.info('start..')
    auto = Automize('计算器')
    if auto.activate_window():
        p = auto.get_window_position()
        print(p)
        with open('debug/screenshot.png', 'wb') as fp:
            fp.write(auto.take_screenshot(*p))
    else:
        logger.info(auto.window_title + '未启动！')
