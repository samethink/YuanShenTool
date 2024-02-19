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

from src.modules.inv import FetchInv, get_inv_filelist
from src.utils.support import SYSTEM_NAME, logger

opr = None
try:
    logger.info('init OPR..')
    from src.modules.opr import OPR

    opr = OPR()
    logger.info('OPR -ok')
except Exception as exc:
    logger.critical(f'An exception occurred: {traceback.format_exc()}')
    opr = False
    opr_error = exc


def check_opr_module() -> (bool, str):
    if opr is None:
        return False, '请等待OPR启动'
    elif opr is False:
        return False, opr_error
    return True, 'OPR正常'


class MainWindow:
    def __init__(self):
        logger.info('init GUI..')
        self.root = tk.Tk()
        self.root.geometry('960x540')
        self.root.resizable(False, False)
        self.root.title('原神工具')
        self.root.iconbitmap('assets/favicon.ico')
        self.set_background('assets/bg_image.png')

        self.__button_position_origin_x = 90
        self.__button_position = [self.__button_position_origin_x, 400]

        self.add_button('购买摆设', callback=lambda: self.__buy_commodities('stuff'),
                        tips='『尘歌壶-洞天百宝』\n自动根据选择的清单购买摆设，需已打开与壶灵的对话列表\n[ESC]键退出')

        self.add_button('购买图纸', callback=lambda: self.__buy_commodities('blueprint'),
                        tips='『尘歌壶-洞天百宝』\n...购买图纸...\n[ESC]键退出')

        self.add_button('获取清单', callback=self.__fetch_inventory,
                        tips='根据分享码获取尘歌壶摹本的需求物品清单，并保存为Excel文件')

        self.add_button('打开清单', callback=self.__open_inventory,
                        tips='使用系统默认方式打开Excel清单')

        self.add_button('播放剧情', callback=self.__play_plots,
                        tips='自动点击过剧情，可[→]加快或[←]减慢\n[CapsLock]键暂停\n[ALT+Q]键退出',
                        next_line=True)

        self.add_button('烹饪料理', callback=self.__cooking,
                        tips='自动烹饪完美料理！\n[ESC]键退出')

        self.__combobox = None
        self.add_combobox()

        self.root.protocol('WM_DELETE_WINDOW', self.__on_closing)
        logger.info('GUI -ok')

    def __on_closing(self):
        if opr and hasattr(opr, 'StopAll'):
            opr.StopAll = True
        self.root.destroy()
        logger.info('UI程序已退出')

    def set_background(self, png_path):
        bg_image = tk.PhotoImage(file=png_path)
        label = tk.Label(self.root, image=bg_image, compound=tk.CENTER)
        label.place(relwidth=1, relheight=1)
        label.image = bg_image

    def add_button(self, text: str, callback: (), tips: str = None, next_line=False):
        if next_line:
            self.__button_position_origin_x += 10
            self.__button_position[0] = self.__button_position_origin_x
            self.__button_position[1] += 45
        button = tk.Button(self.root, text=text, command=callback, foreground='#0E76F8')
        button.place(x=self.__button_position[0], y=self.__button_position[1])
        logger.debug('【%s】 at (%d, %d)' % (text, self.__button_position[0], self.__button_position[1]))
        self.__button_position[0] += 90
        Tooltip(button, text if tips is None else tips)

    def add_combobox(self):
        inv_filelist = get_inv_filelist()
        logger.debug(f'{inv_filelist=}')
        self.__combobox = Combobox(self.root, values=inv_filelist, state='readonly', foreground='#0E76F8')
        self.__combobox.place(x=460, y=404)
        if self.__combobox['values']:
            self.__combobox.current(0)
        self.__combobox.bind('<<ComboboxSelected>>', lambda event: self.__combobox.select_clear())

    def __buy_commodities(self, shelf):
        inv_file = self.__combobox.get()
        if not inv_file:
            messagebox.showwarning('警告', '请先获取清单文件')
            return
        logger.info(f'Used File: {inv_file}')
        symbol, message = check_opr_module()
        if symbol:
            symbol, message = opr.buy_commodities(shelf, inv_file)
            if message == '<refresh_access_token>':
                api_key = simpledialog.askstring('「OCR」需要刷新令牌', 'Api Key:', show='·', parent=self.root)
                secret_key = simpledialog.askstring('继续输入', 'Secret Key:', show='*', parent=self.root)
                opr.ocr.refresh_access_token(api_key, secret_key)
                if opr.ocr.access_token is None:
                    message = '刷新token失败'
                else:
                    opr.ocr.save_ocr_keys(api_key, secret_key)
                    symbol, message = True, '刷新token成功，请重新开始'
        messagebox.showinfo('完成' if symbol else '失败', message)

    def __fetch_inventory(self):
        fetcher = FetchInv()
        share_code = simpledialog.askstring('清单', '摹本分享码：', parent=self.root)
        if share_code is None:
            return
        elif not (share_code.isdigit() and len(share_code) > 9):
            messagebox.showwarning('警告', '分享码错误')
            return

        for _ in range(2):
            symbol, message = fetcher.fetch_inventory(share_code=share_code)
            # symbol, message = True, 'inventory_%s.xlsx' % share_code
            if symbol:
                logger.info(f'获取清单成功，保存路径：「{message}」')
                cur_vals = list(self.__combobox['values'])
                for i, v in enumerate(cur_vals):
                    if v == message:
                        cur_vals.pop(i)
                cur_vals.append(message)
                self.__combobox['values'] = cur_vals
                self.__combobox.current(len(cur_vals) - 1)
                return
            elif message == '<set_cookie>':
                cookie = simpledialog.askstring('清单', '请输入新的有效cookie', parent=self.root)
                fetcher.web.set_cookie(cookie)
            else:
                messagebox.showerror('错误', message)
                logger.error(f'获取失败：「{message}」')
                return
        messagebox.showwarning('警告', 'cookie无效，请检查')

    def __open_inventory(self):
        selected_file = self.__combobox.get()
        err_code = os.system('start cache\\' if SYSTEM_NAME == 'Windows' else 'open cache/' + selected_file)
        if err_code:
            messagebox.showerror('错误', '打开失败')

    def __play_plots(self):
        for thd in threading.enumerate():
            if thd.name == 'pp':
                messagebox.showwarning('警告', '线程正在运行', parent=self.root)
                return

        def pp():
            symbol, message = check_opr_module()
            if symbol:
                symbol, message = opr.play_plots()
            messagebox.showinfo('完成' if symbol else '失败', message)

        pp_thr = threading.Thread(target=pp, name='pp')
        pp_thr.daemon = True
        pp_thr.start()

    def __cooking(self):
        symbol, message = check_opr_module()
        if symbol:
            count = simpledialog.askinteger('烹饪', '请输入次数：',
                                            initialvalue=15, minvalue=1, maxvalue=20, parent=self.root)
            if count is None:
                return
            symbol, message = opr.cooking(count)
        messagebox.showinfo('完成' if symbol else '失败', message)

    def toggle_topmost(self, window, bind_button):
        if window.attributes('-topmost'):
            window.attributes('-topmost', False)
            self.root.deiconify()
            bind_button.pub_config(text='置顶')
        else:
            window.attributes('-topmost', True)
            self.root.iconify()
            bind_button.pub_config(text='取消置顶')

    def display(self):
        self.root.mainloop()


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

        label = tk.Label(self.tooltip, text=self.text, justify='left', relief='solid', borderwidth=0,
                         background='#EFF', foreground='#2CC544')
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


if __name__ == '__main__':
    MainWindow().display()
