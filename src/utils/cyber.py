"""
Author: iota
Create: 2024.1.16 20:40
Project: YuanShenTool
Path: src/utils/cyber.py
IDE: PyCharm
Description: 网络有关方法
"""
import base64
import re
import socket
import urllib.parse


class DotDict(dict):
    """自定义字典类，可以使用"dict.key"的方式来使用字典值"""
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getattr__(self, key):
        return self[key]

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self


def get_my_ipv4_address() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('1.1.1.1', 1))
        return s.getsockname()[0]


def urlencoded(string) -> str:
    return urllib.parse.quote_plus(string)


def bytes_to_base64str(bytes_data) -> str:
    return base64.b64encode(bytes_data).decode('ASCII')


def verify_base64str(string) -> bool:
    return not (len(string) % 4) and re.fullmatch(r'[\dA-Za-z+/]+={0,2}', string)


if __name__ == '__main__':
    print(urlencoded('https://test.net/api?arg=0&word=中 文..'))
