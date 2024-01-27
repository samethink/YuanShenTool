"""
Author: iota
Create: 2023.12.15 6:21
Project: YuanShenTool
Path: src/utils/inv.py
IDE: PyCharm
Description: 需求清单相关方法
"""
import difflib
import re

from src.utils.tool import dump_yaml_file, load_yaml_file


def update_inventory_data(origin_inventory: dict[str:str], raw_string):
    useless_words = ['商店', '图纸', '摆设', '洞天', '百宝']
    for word in useless_words:
        raw_string = raw_string.replace(word, '')

    for line in raw_string.split('\n'):
        req_name = chinese_only(line)
        if not req_name:
            continue

        number = int(temp) if (temp := find_number_in(line)) else 1
        req_nums_str = origin_inventory.get(req_name)
        if req_nums_str is None:
            needed_num, existing_num = number, 0
        else:
            old_need_num, old_existing_num = map(int, req_nums_str.split('\\'))
            needed_num, existing_num = number + old_need_num, old_existing_num
        origin_inventory[req_name] = '%d\\%d' % (needed_num, existing_num)


INVENTORY_FILEPATH = 'resource/inventory.yaml'


def update_inventory_file(text, mode='a'):
    match mode:
        case 'a':
            inventory = load_yaml_file(INVENTORY_FILEPATH)
        case 'w':
            inventory = {}
        case _:
            return False
    update_inventory_data(inventory, text)
    if not inventory:
        return False
    dump_yaml_file(INVENTORY_FILEPATH, inventory, orderly=True)
    return True


def get_numerical_inventory() -> dict[str:dict[str:int]]:
    inventory = load_yaml_file(INVENTORY_FILEPATH)
    numerical_inventory = {}
    for key in inventory:
        needed_num, existing_num = map(int, inventory[key].split('\\'))
        if needed_num > existing_num:
            numerical_inventory[key] = {'needed': needed_num, 'existing': existing_num}
    return numerical_inventory


def save_numerical_inventory(numerical_inventory: dict[str:dict[str:int]]):
    for key in numerical_inventory:
        numerical_inventory[key] = '%(needed)s\\%(existing)s' % (numerical_inventory[key])
    dump_yaml_file(INVENTORY_FILEPATH, numerical_inventory, orderly=True)


def match_requirement(inventory, text):
    """从需求清单里找出与给定文本最相似的结果"""
    threshold_value = 0.72  # 文本匹配度阈值
    ret = None
    if not text.isdigit():
        for req_name in inventory:
            score = calc_similarity(chinese_only(text), req_name)
            if score > threshold_value:
                ret = req_name
                threshold_value = score
    return ret, threshold_value if ret else 0


def find_number_in(text, num_order=1) -> str:
    numbers = re.findall(r'\d+', text)
    if len(numbers) >= num_order:
        return numbers[num_order - 1]


def chinese_only(text: str) -> str:
    """过滤所有非汉字字符"""
    return ''.join([c for c in text if 0x4e00 <= ord(c) <= 0x9fa5])


def calc_similarity(s1: iter, s2: iter) -> float:
    """计算两个可迭代对象的相似度"""
    return difflib.SequenceMatcher(None, s1, s2).ratio()


INVENTORY_TEXT_PATTERN = re.compile(r'^\n*([\u4e00-\u9fa5]+:\s+\d+\s*\\\s*\d+\s*\n)+$')


def validate_text_inventory(text):
    return re.fullmatch(INVENTORY_TEXT_PATTERN, text)


def read_text_inventory():
    with open(INVENTORY_FILEPATH, 'r', encoding='UTF-8') as fp:
        return fp.read()


def save_text_inventory(source_inventory):
    with open(INVENTORY_FILEPATH, 'w', encoding='UTF-8') as fp:
        fp.write(source_inventory)


if __name__ == '__main__':
    inv = get_numerical_inventory()
    req, sco = match_requirement(inv, '寂修石')
    print(req, sco)
