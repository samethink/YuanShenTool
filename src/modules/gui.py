"""
Author: iota
Create: 2023.12.14 19:16
Project: YuanShenTool
Path: src/modules/gui.py
IDE: PyCharm
Description: 实现图形界面
"""
import os
import threading
import tkinter as tk
import traceback
from tkinter import messagebox, simpledialog
from tkinter.ttk import Combobox

from src.modules.inv import FetchInv
from src.modules.opr import OPR
from src.utils.support import SYSTEM_NAME, logger


class MainWindow:
    def __init__(self):
        logger.info('init GUI..')
        self.opr = None
        self.__init_opr()
        self.inv_fetcher = FetchInv()

        self.root = tk.Tk()
        self.root.geometry('960x540')
        self.root.resizable(False, False)
        self.root.title('原神工具')
        self.root.iconbitmap('assets/favicon.ico')

        self.set_background('assets/bg_image.png')
        self.add_buttons()
        self.__combobox = None
        self.add_combobox()

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
        origin_x = 90
        button_position = [origin_x, 400]

        def put(text: str, callback: (), tips: str = None, next_line=False):
            nonlocal origin_x, button_position
            if next_line:
                origin_x += 10
                button_position[0] = origin_x
                button_position[1] += 40
            button = tk.Button(self.root, text=text, command=callback)
            button.place(x=button_position[0], y=button_position[1])
            button_position[0] += 90
            Tooltip(button, text if tips is None else tips)

        put('购买摆设', callback=lambda: self.buy_commodities('stuff'),
            tips='『尘歌壶-洞天百宝』\n自动根据清单购买摆设，需已打开与壶灵的对话列表\n[ESC]键退出')

        put('购买图纸', callback=lambda: self.buy_commodities('blueprint'),
            tips='『尘歌壶-洞天百宝』\n自动根据清单购买摆设图纸，需已打开与壶灵的对话列表\n[ESC]键退出')

        put('获取清单', callback=self.fetch_inventory,
            tips='根据分享码获取尘歌壶摹本的需求物品清单，并保存为Excel文件\n需要设置cookie')

        put('打开清单', callback=self.open_inventory,
            tips='使用系统默认方式打开Excel清单')

        put('播放剧情', callback=self.play_plots,
            tips='自动点击过剧情，可[→]加快或[←]减慢\n[CapsLock]键暂停\n[ALT+Q]键退出',
            next_line=True)

        put('烹饪料理', callback=self.cooking,
            tips='自动烹饪完美料理！\n[ESC]键退出')

    def add_combobox(self):
        inv_filelist = [filename for filename in os.listdir('cache/') if filename.startswith('inventory')]
        logger.debug(inv_filelist)
        self.__combobox = Combobox(self.root, values=inv_filelist, state='readonly')
        self.__combobox.place(x=460, y=404)
        if self.__combobox['values']:
            self.__combobox.current(0)

    def __check_opr_module(self) -> (bool, str):
        if self.opr is None:
            return False, '请以管理员权限启动'
        return True, 'OPR已启动'

    def buy_commodities(self, shelf):
        symbol, message = self.__check_opr_module()
        inv_file = self.__combobox.get()
        if not inv_file:
            messagebox.showwarning('提示', '请先获取清单文件')
            return
        logger.info(f'清单文件：「{inv_file}」')
        if symbol:
            try:
                symbol, message = self.opr.buy_commodities(shelf, inv_file)
            except Exception as exc:
                symbol, message = False, exc
                logger.error(f'An exception occurred: {traceback.format_exc()}')
        messagebox.showinfo('完成' if symbol else '失败', message)

    def fetch_inventory(self):
        share_code = simpledialog.askstring('输入', '分享码：')
        if not share_code:
            return
        elif not (share_code.isdigit() and len(share_code) > 9):
            messagebox.showwarning('提示', '分享码错误')
            return

        for _ in range(2):
            symbol, message = self.inv_fetcher.download_inventory(share_code=share_code)
            # symbol, message = True, 'inventory_%s.xlsx' % share_code
            if symbol:
                logger.info(f'获取清单成功，保存路径：「{message}」')
                cur_vals = list(self.__combobox['values'])
                cur_vals.append(message)
                self.__combobox['values'] = cur_vals
                self.__combobox.current(len(cur_vals) - 1)
                return
            elif message == '<set_cookie>':
                cookie = simpledialog.askstring('输入', '请输入新的有效cookie')
                self.inv_fetcher.web.set_cookie(cookie)
            else:
                messagebox.showerror('失败', message)
                logger.error(f'获取失败：「{message}」')
                return
        messagebox.showwarning('cookie无效，请检查')

    def open_inventory(self):
        selected_file = self.__combobox.get()
        os.system('start cache\\' if SYSTEM_NAME == 'Windows' else 'open cache/' + selected_file)

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

    def __toggle_topmost(self, window, bind_button):
        if window.attributes('-topmost'):
            window.attributes('-topmost', False)
            self.root.deiconify()
            bind_button.config(text='置顶')
        else:
            window.attributes('-topmost', True)
            self.root.iconify()
            bind_button.config(text='取消置顶')


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
