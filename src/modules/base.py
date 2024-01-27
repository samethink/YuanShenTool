"""
Author: iota
Create: 2023.12.14 15:17
Project: YuanShenTool
Path: src/modules/base.py
IDE: PyCharm
Description: 定义窗口基础动作
"""
import ctypes
import logging
import os
import sys
import time

import mss
import mss.tools
import win32api
import win32con
import win32gui

from src.utils.tool import read_config


def get_logger() -> logging.Logger:
    ret = logging.getLogger(__file__)
    ret.setLevel(config['log_level'])
    formatter = logging.Formatter(config['log_format'], style='$')

    if not os.path.exists('debug/'):
        os.mkdir('debug/')
    file_handle = logging.FileHandler('debug/record.log', mode='w', encoding='UTF-8')
    file_handle.setFormatter(formatter)
    ret.addHandler(file_handle)

    stream_handle = logging.StreamHandler(sys.stdout)
    stream_handle.setFormatter(formatter)
    ret.addHandler(stream_handle)
    return ret


config = read_config('config/config.yaml')
logger = get_logger()


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

        self.ACTION_DELAY = config['action_delay']
        self.SCREEN_SIZE = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

    def refresh_window_handle(self):
        self.window_handle = win32gui.FindWindow(self.window_classname, self.window_title)
        logger.info(f'句柄={self.window_handle}')

    def activate_window(self) -> bool:
        if self.window_handle:
            win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self.window_handle)
            self.waiting(1)
            return True
        return False

    def get_window_position(self) -> tuple | None:
        return win32gui.GetWindowRect(self.window_handle)

    def is_window_on_top(self) -> bool:
        return self.window_handle == win32gui.GetForegroundWindow()

    def move_to(self, x: int, y: int):
        win32api.SetCursorPos((x, y))
        self.waiting(0)

    def click(self, x: int, y: int):
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        self.waiting(1)

    def scroll(self, count: int, duration: float = None):
        if duration is None:
            duration = self.ACTION_DELAY
        symbol = 1 if count > 0 else -1
        count = abs(count)
        delay = duration / count
        for _ in range(count):
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, symbol)
            time.sleep(delay)
        self.waiting(1)

    def waiting(self, multiple: int | float = 1):
        time.sleep(self.ACTION_DELAY * multiple)

    mss_sct = mss.mss()

    def take_screenshot(self, x1, y1, x2, y2) -> bytes:
        sct_img = self.mss_sct.grab((x1, y1, x2, y2))
        return mss.tools.to_png(sct_img.rgb, sct_img.size)


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
