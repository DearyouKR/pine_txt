import os
import json
from datetime import datetime, timedelta


def process_long_short_data(main_folder_path, all_path):
    # 获取当前时间
    current_time = datetime.now()
    # 最近7天的时间戳范围
    recent_seven_days_start = int((current_time - timedelta(days=15)).timestamp() * 1000)

    # 遍历主文件夹中的所有子文件夹
    for symbol_folder in os.listdir(main_folder_path):
        # print(symbol_folder)
        all_data = []

        symbol_folder_path = os.path.join(main_folder_path, symbol_folder)

        # # 跳过名为"long_short_all"的文件夹
        # if symbol_folder.lower() == "long_short_all":
        #     continue

        if os.path.isdir(symbol_folder_path):
            # 遍历子文件夹中的所有JSON文件
            for file_name in os.listdir(symbol_folder_path):
                file_path = os.path.join(symbol_folder_path, file_name)

                if file_name.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        try:
                            data = json.load(file)
                            all_data.extend(data)  # 将数据追加到all_data中
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON from file: {file_path}")

        # 对数据按begin字段从小到大排序
        all_data.sort(key=lambda x: x.get('begin', 0))

        # 筛选最近7日的数据
        recent_data = [item for item in all_data if item.get('begin', 0) >= recent_seven_days_start]

        # 写入到子文件夹目录下的all.json文件
        output_file_path = os.path.join(all_path, f"{symbol_folder}_all.json")
        # print(f"output_file_path: {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(recent_data, output_file, indent=4, ensure_ascii=False)


def process_data(data_list, timestamp):
    # 筛选出时间戳在指定范围内的数据
    time_threshold = timestamp - (300 * 15 * 60 * 1000)
    filtered_data = [data for data in data_list if time_threshold <= data["begin"] <= timestamp]

    # if len(filtered_data) < 300:
    #     raise ValueError("没有足够的数据满足条件")

    # 仅保留最近的300条数据
    filtered_data = filtered_data[-300:]

    # 分别获取 netLongsClose 和 netShortsClose 并转换为正值
    net_longs_close_values = [abs(data["netLongsClose"]) for data in filtered_data]
    net_shorts_close_values = [abs(data["netShortsClose"]) for data in filtered_data]

    # 计算平均值
    avg_net_longs_close = sum(net_longs_close_values) / len(net_longs_close_values)
    avg_net_shorts_close = sum(net_shorts_close_values) / len(net_shorts_close_values)


    # 分别获取 netLongsClose 和 netShortsClose 并转换为正值
    net_longs_close_values_2 = [abs(data["netLongsClose"]) for data in filtered_data if abs(data["netLongsClose"]) >= avg_net_longs_close]
    net_shorts_close_values_2 = [abs(data["netShortsClose"]) for data in filtered_data if abs(data["netShortsClose"]) >= avg_net_shorts_close]

    # 计算平均值
    avg_net_longs_close_2 = sum(net_longs_close_values_2) / len(net_longs_close_values_2)
    avg_net_shorts_close_2 = sum(net_shorts_close_values_2) / len(net_shorts_close_values_2)


    # 获取指定时间戳的数据
    specified_data = next((data for data in data_list if data["begin"] == timestamp), None)

    # print(specified_data)

    # if not specified_data:
    #     raise ValueError("指定时间戳的数据未找到")

    specified_net_longs_close = specified_data["netLongsClose"]
    specified_net_shorts_close = specified_data["netShortsClose"]

    # 计算结果
    result_longs = round(specified_net_longs_close /avg_net_longs_close_2, 1)
    result_shorts = round(specified_net_shorts_close / avg_net_shorts_close_2, 1)
    # print(f"l:{result_longs}, s:{result_shorts}\n\n")

    return result_longs, result_shorts


def long_short_value(main_folder_path):

    value_data = {}

    # 遍历主文件夹中的所有子文件夹
    for symbol_folder in os.listdir(main_folder_path):

        symbol_name = symbol_folder.split("_")[0]  # 获取 "_" 前面的部分
        # print(symbol_folder)

        symbol_folder_path = os.path.join(main_folder_path, symbol_folder)

        # print(symbol_folder_path)

        with open(symbol_folder_path, "r") as file:
            symbol_values = json.load(file)

        # print(len(symbol_values))


        start_len = 0
        for data in symbol_values:
            start_len += 1
            if start_len > 350:
                new_time = data["begin"]
                # print(new_time)
                result_longs, result_shorts = process_data(symbol_values, new_time)

                if new_time not in value_data:
                    value_data[new_time] = {}
                value_data[new_time].update({
                    f"{symbol_name}_l": result_longs,
                    f"{symbol_name}_s": result_shorts
                })


    # 将 value_data 写入 value_data.json 文件
    # output_file_path = os.path.join(main_folder_path, "value_data.json")
    with open("data/value_all.json", "w", encoding="utf-8") as output_file:
        json.dump(value_data, output_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main_path = "long_short"
    new_all_path = "long_short_all"
    process_long_short_data(main_path, new_all_path)
    long_short_value(new_all_path)
