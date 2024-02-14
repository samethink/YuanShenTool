"""
Author: iota
Create: 2023.12.14 15:35
Project: YuanShenTool
Path: src/utils/common.py
IDE: PyCharm
Description: 通用工具方法
"""
import json
from os import path

import yaml


def get_abspath(ref_path, rel_path):
    return path.abspath(path.join(path.dirname(ref_path), rel_path))


def load_yaml_from_file(file_path):
    with open(file_path, 'r', encoding='UTF-8') as fp:
        return yaml.safe_load(fp)


def dump_yaml_to_file(file_path, data, orderly=False):
    with open(file_path, 'w', encoding='UTF-8') as fp:
        yaml.safe_dump(data, stream=fp, allow_unicode=True, sort_keys=orderly)


def load_json_from_file(file_path):
    with open(file_path, 'r', encoding='UTF-8') as fp:
        return json.load(fp)


def dump_json_to_file(file_path, data):
    with open(file_path, 'w', encoding='UTF-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=4)


def read_config(file_path) -> dict | None:
    suffix = file_path[file_path.rfind('.'):]
    match suffix:
        case '.json':
            return load_json_from_file(file_path)
        case '.yaml' | '.yml':
            return load_yaml_from_file(file_path)
        case '.ini' | '.cfg':
            return None
        case _:
            return None


def save_config(file_path, data):
    suffix = file_path[file_path.rfind('.'):]
    match suffix:
        case '.json':
            dump_json_to_file(file_path, data)
        case '.yaml' | '.yml':
            dump_yaml_to_file(file_path, data)
        case '.ini' | '.cfg':
            return None
        case _:
            return None


if __name__ == '__main__':
    pass
