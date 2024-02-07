"""
Author: iota
Create: 2023.12.14 19:16
Project: YuanShenTool
Path: src/modules/gui.py
IDE: PyCharm
Description: 实现图形界面
"""
import threading
import tkinter as tk
import traceback
from tkinter import messagebox, simpledialog

import yaml

from src.modules.base import logger
from src.modules.opr import OPR
from src.utils.inv import *


class MainWindow:
    def __init__(self):
        logger.info('init GUI..')
        self.opr = None
        self.__init_opr()

        self.root = tk.Tk()
        self.root.geometry('960x540')
        self.root.resizable(False, False)
        self.root.title('原神工具')
        self.root.iconbitmap('resource/favicon.ico')

        self.set_background('resource/background.png')
        self.add_buttons()

        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        logger.info('GUI -ok')

    def __init_opr(self):
        try:
            logger.info('init OPR..')
            self.opr = OPR()
            logger.info('OPR -ok')
        except Exception as exc:
            logger.critical(f'OPR初始化错误：{exc}')
            logger.error(f'An exception occurred: {traceback.format_exc()}')

    def set_background(self, png_path):
        bg_image = tk.PhotoImage(file=png_path)
        label = tk.Label(self.root, image=bg_image, compound=tk.CENTER)
        label.place(relwidth=1, relheight=1)
        label.image = bg_image

    def add_buttons(self):
        origin_x = 80
        button_position = [origin_x, 400]

        def put(text: str, callback: (), tips: str = None, next_line=False):
            nonlocal origin_x, button_position
            if next_line:
                origin_x += 10
                button_position[0] = origin_x
                button_position[1] += 40
            button = tk.Button(self.root, text=text, command=callback)
            button.place(x=button_position[0], y=button_position[1])
            button_position[0] += 80
            Tooltip(button, text if tips is None else tips)

        put('购买摆设', callback=lambda: self.buy_commodities('stuff'),
            tips='『尘歌壶-洞天百宝』\n自动根据清单购买摆设，需已打开与壶灵的对话列表\n[ESC]键退出')

        put('购买图纸', callback=lambda: self.buy_commodities('blueprint'),
            tips='『尘歌壶-洞天百宝』\n自动根据清单购买摆设图纸，需已打开与壶灵的对话列表\n[ESC]键退出')

        put('录入清单', callback=self.open_input_textbox,
            tips='输入原始文本，格式化为工具可用的需求清单')

        put('打开清单', callback=self.open_edit_textbox,
            tips='查看需求清单，可编辑并保存')

        put('播放剧情', callback=self.play_plots,
            tips='自动点击过剧情，可[→]加快或[←]减慢\n[CapsLock]键暂停\n[ALT+Q]键退出',
            next_line=True)

        put('烹饪料理', callback=self.cooking,
            tips='自动烹饪完美料理！\n[ESC]键退出')

    def __check_opr_module(self) -> (bool, str):
        if self.opr is None:
            return False, '请以管理员权限启动'
        return True, 'OPR已启动'

    def buy_commodities(self, shelf):
        symbol, message = self.__check_opr_module()
        if symbol:
            try:
                symbol, message = self.opr.buy_commodities(shelf)
            except Exception as exc:
                symbol, message = False, exc
                logger.error(f'An exception occurred: {traceback.format_exc()}')
        messagebox.showinfo('完成' if symbol else '失败', message)

    def __toggle_topmost(self, window, bind_button):
        if window.attributes('-topmost'):
            window.attributes('-topmost', False)
            self.root.deiconify()
            bind_button.config(text='置顶')
        else:
            window.attributes('-topmost', True)
            self.root.iconify()
            bind_button.config(text='取消置顶')

    def __make_textbox(self, title):
        sub_win = tk.Toplevel(self.root)
        sub_win.title(title)
        sub_win.geometry('400x600')
        textbox = tk.Text(sub_win, font=('SimSun', 12, 'normal'), spacing1=0, spacing2=5, spacing3=5)
        textbox.pack(fill='both', expand=True)
        btn_frame = tk.Frame(sub_win)
        btn_frame.pack(side='bottom', fill='x')
        topmost_button = tk.Button(btn_frame, text='置顶',
                                   command=lambda: self.__toggle_topmost(sub_win, topmost_button))
        topmost_button.pack(side='left', padx=10)
        cancel_button = tk.Button(btn_frame, text='取消', command=sub_win.destroy)
        cancel_button.pack(side='right', padx=10)
        return sub_win, textbox, btn_frame

    def open_input_textbox(self):
        sub_win, textbox, button_frame = self.__make_textbox(title='录入清单')

        def save_data(mode):
            text = textbox.get('1.0', tk.END).strip()
            if text:
                if mode == 'w' and messagebox.askyesno('确定', '点击确定将覆盖原来的清单'):
                    res = update_inventory_file(text, 'w')
                else:
                    res = update_inventory_file(text, 'a')
                if res:
                    logger.info(f'录入数据已保存 {mode=}')
                    sub_win.destroy()
                else:
                    messagebox.showwarning('失败', '请检查数据')

        update_button = tk.Button(button_frame, text='更新', command=lambda: save_data(mode='a'))
        update_button.pack(side='right', padx=0)
        save_button = tk.Button(button_frame, text='覆盖', command=lambda: save_data(mode='w'))
        save_button.pack(side='right', padx=10)
        sub_win.grab_set()
        sub_win.wait_window()

    def open_edit_textbox(self):
        sub_win, textbox, button_frame = self.__make_textbox(title='编辑清单')

        try:
            data = yaml.safe_load(read_text_inventory())
            textbox.tag_configure('key', foreground='blue')
            textbox.tag_configure('value', foreground='red')
            for key, value in data.items():
                textbox.insert(tk.END, f'{key}: ', 'key')
                textbox.insert(tk.END, f'{value}\n', 'value')
        except yaml.YAMLError as ye:
            logger.info(ye)
        except AttributeError:
            pass

        def save_data():
            text = textbox.get('1.0', tk.END).replace(':', ': ').replace('：', ': ')
            logger.debug(f'{text=}')
            if text != '\n':
                if validate_text_inventory(text):
                    save_text_inventory(text)
                    sub_win.destroy()
                else:
                    messagebox.showwarning('提示', '格式不正确\n纯中文物品名: 需求数量\\已有数量')

        save_button = tk.Button(button_frame, text='保存', command=save_data)
        save_button.pack(side='right', padx=0)
        sub_win.grab_set()
        sub_win.wait_window()

    def play_plots(self):
        for thd in threading.enumerate():
            if thd.name == 'pp':
                messagebox.showinfo('提示', '线程正在运行')
                return

        def pp():
            symbol, message = self.__check_opr_module()
            if symbol:
                symbol, message = self.opr.play_plots()
            messagebox.showinfo('完成' if symbol else '失败', message)

        pp_thr = threading.Thread(target=pp, name='pp')
        pp_thr.daemon = True
        pp_thr.start()

    def cooking(self):
        symbol, message = self.__check_opr_module()
        if symbol:
            count = simpledialog.askinteger(' ', '请输入次数：', initialvalue=15, minvalue=1, maxvalue=20)
            if count is None:
                return
            symbol, message = self.opr.cooking(count)
        messagebox.showinfo('完成' if symbol else '失败', message)

    def display(self):
        self.root.mainloop()

    def on_closing(self):
        if isinstance(self.opr, OPR):
            self.opr.StopAll = True
        self.root.destroy()
        logger.info('UI程序已退出')


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox('insert')
        x += self.widget.winfo_rootx()
        y += self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f'+{x}+{y}')

        label = tk.Label(self.tooltip, text=self.text, justify='left', background='#eff', relief='solid', borderwidth=0)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


if __name__ == '__main__':
    MainWindow().display()
