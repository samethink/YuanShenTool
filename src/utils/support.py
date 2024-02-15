"""
Author: ithink
Create: 2024/2/14 17:20
Project: YuanShenTool
Path: src/utils/support.py
IDE: PyCharm
Description: 
"""
import logging
import os
import platform
import sys

from src.utils.common import read_config

pub_config = read_config('config/public.yml')


def __get_logger() -> logging.Logger:
    ret = logging.getLogger(__file__)
    ret.setLevel(pub_config['log_level'])
    formatter = logging.Formatter(pub_config['log_format'], style='$')

    if not os.path.exists('debug/'):
        os.mkdir('debug/')
    file_handle = logging.FileHandler('debug/record.log', mode='w', encoding='UTF-8')
    file_handle.setFormatter(formatter)
    ret.addHandler(file_handle)

    stream_handle = logging.StreamHandler(sys.stdout)
    stream_handle.setFormatter(formatter)
    ret.addHandler(stream_handle)
    return ret


logger = __get_logger()

DEBUG_MODE = pub_config['debug_mode']
SYSTEM_NAME = platform.system()
