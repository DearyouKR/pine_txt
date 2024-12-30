import os
import json
from datetime import datetime, timedelta

def process_data(data_list, timestamp):
    # 筛选出时间戳在指定范围内的数据
    time_threshold = timestamp - (300 * 15 * 60 * 1000)
    filtered_data = [data for data in data_list if time_threshold <= data["begin"] <= timestamp]

    if len(filtered_data) < 300:
        raise ValueError("没有足够的数据满足条件")

    # 仅保留最近的300条数据
    filtered_data = filtered_data[-300:]

    # 分别获取 netLongsClose 和 netShortsClose 并转换为正值
    net_longs_close_values = [abs(data["netLongsClose"]) for data in filtered_data]
    net_shorts_close_values = [abs(data["netShortsClose"]) for data in filtered_data]

    # 计算平均值
    avg_net_longs_close = sum(net_longs_close_values) / len(net_longs_close_values)
    avg_net_shorts_close = sum(net_shorts_close_values) / len(net_shorts_close_values)

    # 获取指定时间戳的数据
    specified_data = next((data for data in data_list if data["begin"] == timestamp), None)

    # print(specified_data)

    # if not specified_data:
    #     raise ValueError("指定时间戳的数据未找到")

    specified_net_longs_close = abs(specified_data["netLongsClose"])
    specified_net_shorts_close = abs(specified_data["netShortsClose"])

    # 计算结果
    result_longs =round(specified_net_longs_close / avg_net_longs_close, 1)
    result_shorts = round(specified_net_shorts_close / avg_net_shorts_close, 1)
    print(f"l:{result_longs}, s:{result_shorts}\n\n")

    return result_longs, result_shorts




with open("long_short_all/BTC_all.json", "r", encoding="utf-8") as file:
    symbol_values = json.load(file)
start_len = 0
for data in symbol_values:
    start_len += 1
    if start_len > 300:
        new_time = data["begin"]
        # print(new_time)
        process_data(symbol_values, new_time)





# def long_short_ma_json(main_folder_path):
#     ma_data = {}
#
#     # 遍历主文件夹中的所有子文件夹
#     for symbol_folder in os.listdir(main_folder_path):
#         symbol_name = symbol_folder.split("_")[0]  # 获取 "_" 前面的部分
#         # print(symbol_folder)
#
#         symbol_folder_path = os.path.join(main_folder_path, symbol_folder)
#
#         # print(symbol_folder_path)
#
#         with open(symbol_folder_path, "r", encoding="utf-8") as file:
#             symbol_values = json.load(file)
#
#             # print(len(symbol_values))
#
#
# if __name__ == "__main__":
#     main_path = "long_short"
#     new_all_path = "long_short_all"
#     long_short_ma_json(new_all_path)
