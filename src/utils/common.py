"""
Author: iota
Create: 2023.12.14 15:35
Project: YuanShenTool
Path: src/utils/common.py
IDE: PyCharm
Description: 通用工具方法
"""
import json

import yaml


def get_abspath(ref_path, rel_path):
    return ref_path[:ref_path.rfind('/') + 1] + rel_path


def load_yaml_from_file(filepath):
    with open(filepath, 'r', encoding='UTF-8') as fp:
        return yaml.safe_load(fp)


def dump_yaml_to_file(filepath, data, orderly=False):
    with open(filepath, 'w', encoding='UTF-8') as fp:
        yaml.safe_dump(data, stream=fp, allow_unicode=True, sort_keys=orderly)


def load_json_from_file(filepath):
    with open(filepath, 'r', encoding='UTF-8') as fp:
        return json.load(fp)


def dump_json_to_file(filepath, data):
    with open(filepath, 'w', encoding='UTF-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=4)


def read_config(filepath):
    suffix = filepath[filepath.rfind('.'):]
    match suffix:
        case '.yml' | '.yaml':
            return load_yaml_from_file(filepath)
        case '.cfg' | '.ini':
            return None
        case '.json':
            return load_json_from_file(filepath)
        case _:
            return None


def save_config(filepath, data):
    suffix = filepath[filepath.rfind('.'):]
    match suffix:
        case '.yml' | '.yaml':
            dump_yaml_to_file(filepath, data)
        case '.cfg' | '.ini':
            pass
        case '.json':
            dump_json_to_file(filepath, data)
        case _:
            ...


if __name__ == '__main__':
    print(get_abspath(__file__, '../../config.yml'))
