from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from seleniumwire import webdriver as wire_webdriver

import time
import gzip
import random
from io import BytesIO
import pprint
import json
import pandas as pd
from dingtalkchatbot.chatbot import DingtalkChatbot
from coinank.other import get_previous_interval_timestamp, format_timestamp, format_timestamp_ny
from coinank.v2ray import proxy_run, proxy_kill
from coinank.wxchat import push_message, wxpusher_send_by_webapi

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Union

# main_path = "./"
main_path = "/root/coinank/main/"


def categorize_kline_data(folder_path: Union[str, bytes, os.PathLike], data: list, symbol: str):
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
    for record in data:
        # 将毫秒时间戳转换为日期字符串（北京时间）
        timestamp = record.get("begin")
        if timestamp is not None:
            beijing_time = datetime.fromtimestamp(timestamp / 1000, timezone.utc) + beijing_offset
            date_str = beijing_time.strftime("%m-%d")
            if date_str not in daily_data:
                daily_data[date_str] = []
            daily_data[date_str].append(record)

    # 按日期保存为JSON文件
    for date_str, records in daily_data.items():
        file_path = os.path.join(symbol_folder_path, f"{date_str}.json")

        # 检查文件是否存在
        if os.path.exists(file_path):
            # 如果文件存在，加载现有数据
            with open(file_path, "r", encoding="utf-8") as f:
                existing_records = json.load(f)

            # 使用字典以 "begin" 为键，合并去重
            combined_records = {record["begin"]: record for record in (existing_records + records)}
            # 转换回列表进行保存
            records = list(combined_records.values())

        # 保存数据到文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)

        # print(f"文件 {file_path} 已写入，记录数: {len(records)}")


def process_data(data_list):
    new_data = {}
    for item in data_list:
        begin = item.get('begin')
        if begin is not None:
            new_data[begin] = {
                'netLongsClose': item.get('netLongsClose', 0),
                'netShortsClose': item.get('netShortsClose', 0)
            }
    return new_data


def data_get_3(data, end_time):
    long_list_1 = []
    short_list_1 = []

    upper_data = None

    for t, v in data.items():
        long_list_1.append(abs(v["netLongsClose"]))
        short_list_1.append(abs(v["netShortsClose"]))

        if t == end_time:
            upper_data = v

    long_ma_1 = sum(long_list_1) / len(long_list_1)
    short_ma_1 = sum(short_list_1) / len(short_list_1)

    long_list_2 = []
    short_list_2 = []

    # print(upper_data)

    for t, v in data.items():
        netLongsClose = abs(v["netLongsClose"])
        netShortsClose = abs(v["netShortsClose"])

        if netLongsClose >= long_ma_1:
            long_list_2.append(netLongsClose)

        if netShortsClose >= short_ma_1:
            short_list_2.append(netShortsClose)

    long_ma_2 = round(sum(long_list_2) / len(long_list_2), 1)
    short_ma_2 = round(sum(short_list_2) / len(short_list_2), 1)
    # print(long_ma_2)
    # print(short_ma_2)
    ma_2_value = 1

    long_value = round(upper_data["netLongsClose"] / (long_ma_2 * ma_2_value), 1)
    short_value = round(upper_data["netShortsClose"] / (short_ma_2 * ma_2_value), 1)

    return long_value, short_value


def count_sum(condition_dict):
    long_add = {}
    long_minus = {}
    short_add = {}
    short_minus = {}
    dj_value = 0.8 * 0.8

    for key, values in condition_dict.items():
        # 检查 long_value 和 short_value 是否大于 1
        if values["long_value"] >= dj_value:
            long_add[key] = values["long_value"]
        elif values["long_value"] <= -dj_value:
            long_minus[key] = values["long_value"]

        if values["short_value"] >= dj_value:
            short_add[key] = values["short_value"]
        elif values["short_value"] <= -dj_value:
            short_minus[key] = values["short_value"]

    return long_add, long_minus, short_add, short_minus


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


def dd_tuisong(symbol, txt):
    webhook, secret = get_webhook_and_secret(symbol)
    xiaoding_error = DingtalkChatbot(webhook, secret=secret)
    xiaoding_error.send_text(msg=txt, is_at_all=False)


def symbols_txt(data):
    txt = ""
    for key, value in data.items():
        txt += f"{key}: {value}\n"

    return txt


def get_last_symbol(data_list):
    # 检查 data_list 是否为空
    if not data_list:
        return None
    # 获取最后一组数据
    last_item = data_list[-1]
    # 返回 symbol 键对应的值
    return last_item.get('symbol', None)


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

    text_txt = f"{'+' * 8 + text}【{len(sorted_data)}】{'+' * 8}\n{txt}\n"

    # 返回标题和拼接的文本
    return text_txt


def symbols_txt_minus(data, text):
    # # 筛选出比 threshold 大的键值对
    # filtered_data = {key: value for key, value in data.items() if value <= -threshold}

    # 如果筛选后的数据为空，直接返回空字符串
    if not data:
        return ""

    # 按 value 从大到小排序
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=False)

    # 拼接字符串
    txt = ""
    for key, value in sorted_data:
        txt += f"{key}: {value}\n"

    # 去掉最后的换行符
    txt = txt.rstrip("\n")

    text_txt = f"{'-' * 8 + text}【{len(sorted_data)}】{'-' * 8}\n{txt}\n"

    # 返回标题和拼接的文本
    return text_txt


def long_click():
    # 配置浏览器选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 可选，设置为无头模式（不显示浏览器窗口）
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 配置Selenium Wire的代理设置
    seleniumwire_options = {
        'proxy': {
            'http': 'http://127.0.0.1:10809',
            'https': 'http://127.0.0.1:10809',
            'no_proxy': 'localhost,127.0.0.1',  # 不通过代理的地址
            'socks': 'socks5://127.0.0.1:10808'
        }
    }

    # 启动带有Selenium Wire的浏览器
    driver = wire_webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)

    condition_dict = {}
    first_iteration = True  # 标志变量，表示是否为第一次循环
    end_time = int(get_previous_interval_timestamp(15) - (15 * 60))
    # print(end_time)
    end_time_ms = int(end_time * 1000)
    print(end_time_ms)

    symbols_list = []
    with open(f"{main_path}data/symbol.txt", 'r') as file:
        for line in file:
            stripped_line = line.strip()
            if stripped_line:
                symbols_list.append(f"{stripped_line}")

    for i in symbols_list:
        print(f"{i}:")

        try:

            # 打开网页
            driver.get(f"https://coinank.com/en/tv?exchange=Binance&symbol={i}USDT&productType=SWAP")  # 替换为你想访问的网址
            # print("开始点击")

            time.sleep(random.randint(15, 25))

            if first_iteration:
                click_data = {
                    "5m": '/html/body/div[1]/div/div/section/div[1]/div[1]/div/div[2]/div[2]/span/div[2]',
                    "15m": '/html/body/div[1]/div/div/section/div[1]/div[1]/div/div[2]/div[2]/span/div[3]',
                    "30m": '/html/body/div[1]/div/div/section/div[1]/div[1]/div/div[2]/div[2]/span/div[4]',
                    "coinank指标": '/html/body/div[1]/div/div/section/div[1]/div[1]/div/div[2]/div[5]/div/span',
                    "净多头": '/html/body/div[3]/div/div[2]/div/div[2]/div[2]/div/div[2]/div[20]',
                }

                # 第一步点击
                element_to_click_1 = driver.find_element(By.XPATH, click_data["15m"])
                element_to_click_1.click()
                time.sleep(random.randint(3, 6))

                # 第二步点击
                element_to_click_2 = driver.find_element(By.XPATH, click_data["coinank指标"])
                element_to_click_2.click()
                # print("完成 >合约指标< 的点击")
                time.sleep(random.randint(3, 6))

                # 第三步点击
                element_to_click_3 = driver.find_element(By.XPATH, click_data["净多头"])
                element_to_click_3.click()
                # print("完成 >净多头< 的点击")
                time.sleep(random.randint(3, 6))

                first_iteration = False  # 将标志改为 False，后续循环将跳过这段代码

            for request in driver.requests:
                if request.response and request.response.status_code == 200:
                    if "netPositions" in request.url and i in request.url:
                        print(request.url)
                        response_body = BytesIO(request.response.body)
                        try:
                            with gzip.GzipFile(fileobj=response_body) as f:
                                response_text = f.read().decode('utf-8', errors='ignore')
                        except OSError:
                            response_text = request.response.body.decode('utf-8', errors='ignore')

                        data = json.loads(response_text)
                        categorize_kline_data(f"{main_path}data/long_short/", data["data"], i)

                        for d in data["data"]:
                            if d["begin"] == end_time_ms:
                                pprint.pprint(d)

                                # 测试时保留
                                # pprint.pprint(data["data"])
                                new_data = process_data(data["data"])
                                long_value, short_value = data_get_3(new_data, end_time_ms)
                                condition_dict[i] = {"long_value": long_value, "short_value": short_value}

                                # 如果当前币种满足条件，则发生警报
                                symbols_list_appoint = ["BTC", "ETH", "AVAX", "NEAR", "LINK", "WLD", "WIF", "OP",
                                                        "ORDI"]
                                dj_value = 0.8

                                if long_value >= dj_value and i in symbols_list_appoint:
                                    l_txt = f"净【{long_value}】++多仓++【{format_timestamp(end_time)}】"
                                    dd_tuisong(i, l_txt)
                                    if i == "BTC":
                                        push_message("90e5d3c76f4d4efcb6a0a0fe2fb91c7a", l_txt, i)

                                if long_value <= -dj_value and i in symbols_list_appoint:
                                    l_txt = f"净【{long_value}】--多仓--【{format_timestamp(end_time)}】"
                                    dd_tuisong(i, l_txt)
                                    if i == "BTC":
                                        push_message("90e5d3c76f4d4efcb6a0a0fe2fb91c7a", l_txt, i)

                                if short_value >= dj_value and i in symbols_list_appoint:
                                    s_txt = f"净【{short_value}】++空仓++【{format_timestamp(end_time)}】"
                                    dd_tuisong(i, s_txt)
                                    if i == "BTC":
                                        push_message("90e5d3c76f4d4efcb6a0a0fe2fb91c7a", s_txt, i)

                                if short_value <= -dj_value and i in symbols_list_appoint:
                                    s_txt = f"净【{short_value}】--空仓--【{format_timestamp(end_time)}】"
                                    dd_tuisong(i, s_txt)
                                    if i == "BTC":
                                        push_message("90e5d3c76f4d4efcb6a0a0fe2fb91c7a", s_txt, i)

                                break

            time.sleep(random.randint(3, 5))

        except Exception as e:
            print(f'发生错误: {e}')

    # 如果condition_dict满足条件，则发生警报
    long_add, long_minus, short_add, short_minus = count_sum(condition_dict)
    symbols_len = 12
    # if long_add >= symbols_len or long_minus >= symbols_len or short_add >= symbols_len or short_minus >= symbols_len:
    if len(long_add) >= symbols_len or len(long_minus) >= symbols_len or len(short_add) >= symbols_len or len(
            short_minus) >= symbols_len:
        l_yes_txt = f"{symbols_txt_add(long_add, '多仓集体加仓')}"
        l_no_txt = f"{symbols_txt_minus(long_minus, '多仓集体减仓')}"
        s_yes_txt = f"{symbols_txt_add(short_add, '空仓集体加仓')}"
        s_no_txt = f"{symbols_txt_minus(short_minus, '空仓集体减仓')}"

        wx_txt = f"{format_timestamp_ny(end_time)}\n{l_yes_txt}{l_no_txt}{s_yes_txt}{s_no_txt}"

        dd_tuisong("减仓", wx_txt)

        push_message("90e5d3c76f4d4efcb6a0a0fe2fb91c7a", wx_txt, "ALL")

    driver.quit()


if __name__ == "__main__":
    start_time_a = time.time()
    proxy_run()

    long_click()

    proxy_kill()

    end_time_a = time.time()  # 记录脚本结束时间
    run_time = end_time_a - start_time_a  # 计算脚本运行时间
    print(f"run_time：{int(run_time / 60)} M {int(run_time % 60)} S")