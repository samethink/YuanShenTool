"""
Author: iota 
Create: 2023.12.14 20:16
Project: YuanShenTool
Path: src/modules/opr.py
IDE: PyCharm
Description: 定义窗口自动化的具体操作
"""
import threading
import time
import traceback
from typing import Literal

import keyboard

from src.modules.base import Automize, config, logger
from src.modules.ocr import DEBUG_MODE, get_ocr
from src.utils.inv import get_numerical_inventory, match_requirement, save_numerical_inventory


class OPR:
    def __init__(self):
        self.auto = Automize(window_title='原神', window_classname='UnityWndClass', _admin_permission_required=True)
        self.ocr = None
        init_ocr_thr = threading.Thread(target=self.__init_ocr, name='init_ocr')
        init_ocr_thr.daemon = True
        init_ocr_thr.start()
        self.StopAll = False

    def __init_ocr(self):
        try:
            logger.info('init OPR.OCR..')
            self.ocr = get_ocr(config['ocr_platform'])
            logger.info('OPR.OCR -ok')
        except Exception as exc:
            logger.error(f'An exception occurred: {traceback.format_exc()}')
            self.ocr_exception = exc

    def play_plots(self):
        """自动播放剧情

        :return: 返回成功标志，结果消息
        """
        self.auto.refresh_window_handle()
        if not self.auto.activate_window():
            return False, self.auto.window_title + '未启动！'

        logger.info('[开始]播放剧情')
        switch = True
        stop_execution = False
        playing_delay = 0.5

        def pause():
            nonlocal switch
            switch = not switch
            logger.info('[继续]播放剧情' if switch else '[暂停]播放剧情')

        def stop():
            nonlocal stop_execution
            stop_execution = True
            logger.info('[停止]播放剧情')

        def speed_up():
            nonlocal playing_delay
            playing_delay -= 0.4
            if playing_delay < 0:
                playing_delay = 0

        def slow_down():
            nonlocal playing_delay
            playing_delay += 0.4
            if playing_delay > 2:
                playing_delay = 2

        keyboard.add_hotkey('CAPSLOCK', pause)
        keyboard.add_hotkey('ALT+Q', stop)
        keyboard.add_hotkey('LEFT', slow_down)
        keyboard.add_hotkey('RIGHT', speed_up)

        while not (stop_execution or self.StopAll):
            if switch and self.auto.is_window_on_top():
                self.auto.click(1300, 800)
                time.sleep(playing_delay)
            else:
                time.sleep(0.1)

        keyboard.remove_hotkey(pause)
        keyboard.remove_hotkey(stop)
        keyboard.remove_hotkey(slow_down)
        keyboard.remove_hotkey(speed_up)
        return True, '结束自动播放'

    def buy_commodities(self, shelf: Literal['stuff', 'blueprint']):
        """自动读取需求清单，购买洞天摆设或图纸

        需已打开与壶灵的对话列表

        :param shelf: stuff=摆设，blueprint=图纸
        :return: 返回成功标志，结果信息
        """
        if hasattr(self, 'ocr_exception'):
            return False, f'OCR启用不成功：{self.ocr_exception}'
        elif self.ocr is None:
            return False, '请等待OCR完成初始化'
        self.auto.refresh_window_handle()
        if not self.auto.activate_window():
            return False, self.auto.window_title + '未启动！'

        logger.info(self.auto.window_title + '启动！')
        self.auto.click(1300, 650)
        self.auto.waiting(1)
        match shelf:
            case 'stuff':
                self.auto.click(200, 250)
            case 'blueprint':
                self.auto.click(200, 340)
            case _:
                logger.warning(f'unacceptable value: {shelf}')
                return False, 'shelf参数错误'
        self.auto.waiting(1.5)

        return ImplementBuyCommodities(self).main(shelf)


class ImplementBuyCommodities:
    def __init__(self, opr_obj):
        self.opr = opr_obj
        self.inventory = get_numerical_inventory()
        self.ignored_set = set()
        self.stop_execution = False

        # 识别商品的矩形区域
        self.rect_left_top = 510, 100
        self.rect_right_bottom = 970, 950
        # 监听按下ESC时退出
        keyboard.add_hotkey('ESC', self.on_escape)

    def main(self, shelf):
        if not self.inventory:
            return False, '清单是空的'

        first_text = ''
        while not (self.stop_execution or self.opr.StopAll):
            screenshot = self.opr.auto.take_screenshot(*self.rect_left_top, *self.rect_right_bottom)
            detected_items = self.opr.ocr.scan_image(screenshot, ret_detail=True, compression_ratio=0.5)
            if not detected_items:
                return False, '(っ °Д °;)っ解析结果是空的'

            # 根据第一行文字判断列表是否到头
            if first_text and not first_text.isdigit() and first_text == detected_items[0][1]:
                logger.info('列表结束')
                break
            first_text = detected_items[0][1]

            # 遍历所有已识别的项目
            need_to_start_over = self.traversal_every_items(detected_items, shelf)
            if need_to_start_over:
                first_text = ''
                continue

            # 检查有没有买完
            if len(self.inventory) == len(self.ignored_set):
                logger.info('购买完成')
                break

            # 向下滚动列表
            self.opr.auto.move_to(1200, 860)
            self.opr.auto.scroll(-45)

            # 检查是否已售罄
            sellout_image = self.opr.auto.take_screenshot(1200, 110, 1350, 250)
            temp_items = self.opr.ocr.scan_image(sellout_image, ret_detail=False)
            if temp_items and temp_items[0] in ['已售罄', '已掌握该配方']:
                logger.info('剩余商品已无法购买')
                break

        save_numerical_inventory(self.inventory)
        keyboard.remove_hotkey(self.on_escape)
        if self.stop_execution:
            return False, '操作停止'
        else:
            return True, '操作完成'

    def traversal_every_items(self, detected_items, shelf):
        for item in detected_items:
            if self.stop_execution or self.opr.StopAll:
                return False

            rect, text, reliability = item
            if text in self.ignored_set:
                logger.info(f'已忽略：{text}')
                continue

            matched_req, score = match_requirement(self.inventory, text)
            logger.debug(f'识别相似度：({matched_req}) / ({text}) = {score}')
            if matched_req is None:
                continue

            needed_num, existing_num = self.inventory[matched_req].values()
            logger.info('[%s]需求\\已有：%d\\%d' % (matched_req, needed_num, existing_num))
            if needed_num <= existing_num:
                logger.info('物品数量已足够')
                continue

            # 还原文本所处的坐标，点击目标商品
            self.opr.auto.click(self.rect_left_top[0] + rect[2][0], self.rect_left_top[1] + rect[2][1])
            # 点击兑换
            self.opr.auto.click(1800, 1024)
            if shelf == 'stuff':
                # 增加购买数量
                purchase_num, limited_num = self.click_increase_purchase_num_button(needed_num - existing_num)
                self.inventory[matched_req]['existing'] = existing_num + purchase_num
            else:
                purchase_num, limited_num = 1, 1
            logger.info(f'购买数量：{purchase_num}')
            if not DEBUG_MODE:
                # 确定兑换
                self.opr.auto.click(1210, 800)
                # 点击空白
                self.opr.auto.click(1210, 800)
            else:
                # 取消
                self.opr.auto.click(800, 780)
            self.ignored_set.add(text)
            if purchase_num == limited_num:
                return True
        return False

    def click_increase_purchase_num_button(self, real_needed_num):
        max_number_image = self.opr.auto.take_screenshot(1190, 580, 1260, 620)
        temp_items = self.opr.ocr.scan_image(max_number_image, ret_detail=False)
        if temp_items and temp_items[0].isdigit():
            limited_num = int(temp_items[0])
        else:
            limited_num = 6
        purchase_num = min(real_needed_num, limited_num)
        for _ in range(purchase_num - 1):
            self.opr.auto.click(1290, 600)
        return purchase_num, limited_num

    def on_escape(self):
        self.stop_execution = True


if __name__ == '__main__':
    from src.utils.tool import load_yaml_file

    logger.info('start..')
    yuan = OPR()
    reqs = load_yaml_file('resource/inventory.yaml')
    res = yuan.buy_commodities(input('$ stuff/blueprint: \n'))
    logger.info(res)
