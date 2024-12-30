from coinalyze.kline import liquidation_history
from coinalyze.other import get_previous_interval_timestamp, format_timestamp, format_timestamp_ny
from coinalyze.wxchat import push_message, wxpusher_send_by_webapi
import time
import pandas as pd
from dingtalkchatbot.chatbot import DingtalkChatbot
from datetime import datetime, timezone, timedelta
from typing import Union
import os
import json

"""
[{'code': 'P', 'name': 'Poloniex'},
 {'code': 'V', 'name': 'Vertex'},
 {'code': 'D', 'name': 'Bitforex'},
 {'code': 'K', 'name': 'Kraken'},
 {'code': 'U', 'name': 'Bithumb'},
 {'code': 'B', 'name': 'Bitstamp'},
 {'code': 'H', 'name': 'Hyperliquid'},
 {'code': 'L', 'name': 'BitFlyer'},
 {'code': 'M', 'name': 'BtcMarkets'},
 {'code': 'I', 'name': 'Bit2c'},
 {'code': 'E', 'name': 'MercadoBitcoin'},
 {'code': 'N', 'name': 'Independent Reserve'},
 {'code': 'G', 'name': 'Gemini'},
 {'code': 'Y', 'name': 'Gate.io'},
 {'code': '2', 'name': 'Deribit'},
 {'code': '3', 'name': 'OKX'},
 {'code': 'C', 'name': 'Coinbase'},
 {'code': 'F', 'name': 'Bitfinex'},
 {'code': 'J', 'name': 'Luno'},
 {'code': '0', 'name': 'BitMEX'},
 {'code': '7', 'name': 'Phemex'},
 {'code': 'W', 'name': 'WOO X'},
 {'code': '4', 'name': 'Huobi'},
 {'code': '8', 'name': 'dYdX'},
 {'code': '6', 'name': 'Bybit'},
 {'code': 'A', 'name': 'Binance'}]

 "1min" "5min" "15min" "30min" "1hour" "2hour" "4hour" "6hour" "12hour" "daily"
"""

main_path = "/root/liquidation/main/"
start_time_a = time.time()


def categorize_kline_data(folder_path: Union[str, bytes, os.PathLike], data: dict, symbol: str):
    """
    将传入的K线数据按每日时间归类，并存储为JSON文件。

    参数：
    folder_path (Union[str, bytes, os.PathLike]): 存储JSON文件的目标文件夹路径。
    data (list): 包含K线数据的列表。
    symbol (str): 数据对应的symbol，用于创建对应的文件夹。
    """
    # 在主文件夹下创建symbol命名的子文件夹
    symbol_folder_path = os.path.join(folder_path, symbol)
    os.makedirs(symbol_folder_path, exist_ok=True)

    # 用于存储按日期归类的数据
    daily_data = {}

    # 北京时区偏移量（+8小时）
    beijing_offset = timedelta(hours=8)

    # 遍历数据并按日期归类
    for t, v in data.items():
        # 将毫秒时间戳转换为日期字符串（北京时间）
        timestamp = t
        if timestamp is not None:
            beijing_time = datetime.fromtimestamp(timestamp, timezone.utc) + beijing_offset
            date_str = beijing_time.strftime("%m-%d")
            if date_str not in daily_data:
                daily_data[date_str] = []
            wz_data = {"t": t, "l": v["l"], "s": v["s"]}
            daily_data[date_str].append(wz_data)

    # 按日期保存为JSON文件
    for date_str, records in daily_data.items():
        file_path = os.path.join(symbol_folder_path, f"{date_str}.json")

        # 检查文件是否存在
        if os.path.exists(file_path):
            # 如果文件存在，加载现有数据
            with open(file_path, "r", encoding="utf-8") as f:
                existing_records = json.load(f)

            # 使用字典以 "begin" 为键，合并去重
            combined_records = {record["t"]: record for record in (existing_records + records)}
            # 转换回列表进行保存
            records = list(combined_records.values())

        # 保存数据到文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)

        print(f"文件 {file_path} 已写入，记录数: {len(records)}")


def get_webhook_and_secret(symbols):
    """
    从表格中读取指定 symbols 的 Webhook 和 加签。
    如果没有找到对应 symbols 的行，则返回群昵称为“其他”的 Webhook 和 加签。

    参数:
    - xlsx_path: 表格文件路径
    - symbols: 需要匹配的关键字

    返回:
    - (webhook, secret): 如果找到对应行，返回 Webhook 和 加签元组；否则返回群昵称为“其他”的对应值。
    """

    xlsx_path = f"{main_path}data/dd_Webhook.xlsx"
    try:
        # 读取Excel文件
        df = pd.read_excel(xlsx_path)

        # 查找包含 symbols 的行
        matching_rows = df[df['群昵称'].str.contains(symbols, na=False)]

        if not matching_rows.empty:
            # 如果找到匹配的行，取第一行的 Webhook 和 加签
            webhook = matching_rows['Webhook'].values[0]
            secret = matching_rows['加签'].values[0]
        else:
            # 如果未找到，查找群昵称为“其他”的行
            other_rows = df[df['群昵称'] == "其他"]
            if not other_rows.empty:
                webhook = other_rows['Webhook'].values[0]
                secret = other_rows['加签'].values[0]
            else:
                # 如果“其他”行也不存在，返回 None
                webhook = None
                secret = None

        return webhook, secret

    except Exception as e:
        print(f"发生错误: {e}")
        return None, None


def liquidation_time_sum(api_key, symbol, end_time):
    print(symbol)
    data = liquidation_history(api_key, f"{symbol}USDT_PERP.A,{symbol}USDT_PERP.3,{symbol}USDT_PERP.4,{symbol}USDT.6",
                               "15min", int(end_time - (6 * 15 * 60)), int(end_time + (30 * 60)), "true")

    l_list = []
    s_list = []

    data_dict = {}

    for item in data:
        for i in item['history']:
            if i["t"] not in data_dict:
                data_dict[i["t"]] = {"l": i["l"], "s": i["s"]}
            else:
                data_dict[i["t"]]["l"] += i["l"]
                data_dict[i["t"]]["s"] += i["s"]

            if i["t"] == end_time:
                # print(i)
                l_list.append(i["l"])
                s_list.append(i["s"])

    # print(sum(l_list))
    # print(sum(s_list))

    return sum(l_list), sum(s_list), data_dict


def symbols_txt(data):
    txt = ""
    for key, value in data.items():
        txt += f"{key}: {value}\n"

    return txt


def symbols_txt_add(data, text):
    # # 筛选出比 threshold 大的键值对
    # filtered_data = {key: value for key, value in data.items() if value >= threshold}

    # 如果筛选后的数据为空，直接返回空字符串
    if not data:
        return ""

    # 按 value 从大到小排序
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    # 拼接字符串
    txt = ""
    for key, value in sorted_data:
        txt += f"{key}: {value}\n"

    # 去掉最后的换行符
    txt = txt.rstrip("\n")

    text_txt = f"{'*' * 8 + text}【{len(sorted_data)}】{'*' * 8 }\n{txt}\n"

    # 返回标题和拼接的文本
    return text_txt


def liquidation_collective():
    api_key_str = "06af1cc6-35ac-4173-8dc8-5b2a760f5dee"
    with open(f"{main_path}data/ma_values.json", "r") as file:
        ma_values = json.load(file)

    l_yes_dict = {}
    l_no_dict = {}
    s_yes_dict = {}
    s_no_dict = {}

    symbols_list_appoint = ["BTC", "ETH", "AVAX", "NEAR", "LINK", "WLD", "WIF", "OP", "ORDI"]

    end_time = int(get_previous_interval_timestamp(15) - (15 * 60))
    print(end_time)

    for symbol, data in ma_values.items():
        l_ma = data["l"] * 1
        s_ma = data["s"] * 1

        l_value, s_value, data_dict = liquidation_time_sum(api_key_str, symbol, end_time)

        categorize_kline_data(f"{main_path}data/liquidation/", data_dict, symbol)

        if l_value >= l_ma and symbol in symbols_list_appoint:
            print("l_yes")
            l_multiple = round(l_value / l_ma, 1)
            # l_txt = f"【{format_timestamp(end_time)}】猎杀 > 多：【{l_multiple}】"
            l_txt = f"杀【{l_multiple}】##多仓##【{format_timestamp(end_time)}】"

            # push_api_key = "90e5d3c76f4d4efcb6a0a0fe2fb91c7a"
            # push_message(push_api_key, l_txt, symbol)

            webhook, secret = get_webhook_and_secret(symbol)
            xiaoding_error = DingtalkChatbot(webhook, secret=secret)
            xiaoding_error.send_text(msg=l_txt, is_at_all=False)
            if symbol == "BTC":
                app_token = 'AT_gDo5Xp3xflLgYXn5zF4lhQ5PGfSP6u5D'  # 本处改成自己的应用 APP_TOKEN
                uid_myself = 'UID_mGauhYJtXKKXRlTA6e0qFbKEthZr'  # 本处改成自己的 UID
                wxpusher_send_by_webapi(app_token, uid_myself, l_txt)

        if s_value >= s_ma and symbol in symbols_list_appoint:
            print("s_yes")
            s_multiple = round(s_value / s_ma, 1)
            # s_txt = f"【{format_timestamp(end_time)}】猎杀 > 空：【{s_multiple}】"
            s_txt = f"杀【{s_multiple}】##空仓##【{format_timestamp(end_time)}】"

            # push_api_key = "90e5d3c76f4d4efcb6a0a0fe2fb91c7a"
            # push_message(push_api_key, s_txt, symbol)

            webhook, secret = get_webhook_and_secret(symbol)
            xiaoding_error = DingtalkChatbot(webhook, secret=secret)
            xiaoding_error.send_text(msg=s_txt, is_at_all=False)

            if symbol == "BTC":
                app_token = 'AT_gDo5Xp3xflLgYXn5zF4lhQ5PGfSP6u5D'  # 本处改成自己的应用 APP_TOKEN
                uid_myself = 'UID_mGauhYJtXKKXRlTA6e0qFbKEthZr'  # 本处改成自己的 UID
                wxpusher_send_by_webapi(app_token, uid_myself, s_txt)

        if l_value >= l_ma * 0.8:
            l_yes_dict[symbol] = round(l_value / l_ma, 1)
        else:
            l_no_dict[symbol] = round(l_value / l_ma, 1)

        if s_value >= s_ma * 0.8:
            s_yes_dict[symbol] = round(s_value / s_ma, 1)
        else:
            s_no_dict[symbol] = round(s_value / s_ma, 1)

        time.sleep(8)

    symbols_len = 12

    if len(l_yes_dict) >= symbols_len or len(s_yes_dict) >= symbols_len:
        # l_yes_txt = f"多_猎杀【{len(l_yes_dict)}】\n{symbols_txt(l_yes_dict)}\n{'*' * 20}"
        # l_no_txt = f"多_未满足【{len(l_no_dict)}】\n{symbols_txt(l_no_dict)}\n{'*' * 20}"
        # s_yes_txt = f"空_猎杀【{len(s_yes_dict)}】\n{symbols_txt(s_yes_dict)}\n{'*' * 20}"
        # s_no_txt = f"空_未满足【{len(s_no_dict)}】\n{symbols_txt(s_no_dict)}\n{'*' * 20}"

        l_yes_txt = f"{symbols_txt_add(l_yes_dict, '多头集体被爆仓')}"
        l_no_txt = f"{symbols_txt_add(l_no_dict, '多头不满足条件')}"
        s_yes_txt = f"{symbols_txt_add(s_yes_dict, '空头集体被爆仓')}"
        s_no_txt = f"{symbols_txt_add(s_no_dict, '空头不满足条件')}"

        wx_txt = f"{format_timestamp_ny(end_time)}\n{l_yes_txt}{l_no_txt}{s_yes_txt}{s_no_txt}"

        app_token = 'AT_gDo5Xp3xflLgYXn5zF4lhQ5PGfSP6u5D'  # 本处改成自己的应用 APP_TOKEN
        uid_myself = 'UID_mGauhYJtXKKXRlTA6e0qFbKEthZr'  # 本处改成自己的 UID
        wxpusher_send_by_webapi(app_token, uid_myself, wx_txt)

        webhook, secret = get_webhook_and_secret("清算")
        xiaoding_error = DingtalkChatbot(webhook, secret=secret)
        xiaoding_error.send_text(msg=wx_txt, is_at_all=False)


if __name__ == "__main__":
    liquidation_collective()
    end_time_a = time.time()  # 记录脚本结束时间
    run_time = end_time_a - start_time_a  # 计算脚本运行时间
    print(f"run_time：{int(run_time / 60)} M {int(run_time % 60)} S")
