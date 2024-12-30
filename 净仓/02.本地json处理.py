import os
import json
from datetime import datetime, timedelta


def process_long_short_data(main_folder_path, all_path):
    # 获取当前时间
    current_time = datetime.now()
    # 最近7天的时间戳范围
    recent_seven_days_start = int((current_time - timedelta(days=10)).timestamp() * 1000)

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



def data_ma(data):
    long_list_1 = []
    short_list_1 = []

    for d in data:
        long_list_1.append(abs(d["netLongsClose"]))
        short_list_1.append(abs(d["netShortsClose"]))

    long_ma_1 = sum(long_list_1) / len(long_list_1)
    short_ma_1 = sum(short_list_1) / len(short_list_1)

    long_list_2 = []
    short_list_2 = []

    # print(upper_data)

    for d in data:
        netLongsClose = abs(d["netLongsClose"])
        netShortsClose = abs(d["netShortsClose"])

        if netLongsClose >= long_ma_1:
            long_list_2.append(netLongsClose)

        if netShortsClose >= short_ma_1:
            short_list_2.append(netShortsClose)

    long_ma_2 = round(sum(long_list_2) / len(long_list_2), 1)
    short_ma_2 = round(sum(short_list_2) / len(short_list_2), 1)

    return long_ma_2, short_ma_2


def long_short_ma_json(main_folder_path):
    ma_data = {}

    # 遍历主文件夹中的所有子文件夹
    for symbol_folder in os.listdir(main_folder_path):
        symbol_name = symbol_folder.split("_")[0]  # 获取 "_" 前面的部分
        # print(symbol_folder)

        symbol_folder_path = os.path.join(main_folder_path, symbol_folder)

        # print(symbol_folder_path)

        with open(symbol_folder_path, "r", encoding="utf-8") as file:
            symbol_values = json.load(file)

        last_300_values = symbol_values[-300:]

        long_ma_2, short_ma_2 = data_ma(last_300_values)
        # print(long_ma_2)
        # print(short_ma_2)
        # print("\n\n")
        ma_data[symbol_name] = {"l": long_ma_2, "s": short_ma_2}

    with open("data/ma_data.json", 'w', encoding='utf-8') as output_file:
        json.dump(ma_data, output_file, indent=4, ensure_ascii=False)



def long_short_value(main_folder_path):
    with open("data/ma_data.json", 'r', encoding='utf-8') as file:
        ma_data = json.load(file)

    value_data = {}

    # 遍历主文件夹中的所有子文件夹
    for symbol_folder in os.listdir(main_folder_path):
        symbol_data = {}

        symbol_name = symbol_folder.split("_")[0]  # 获取 "_" 前面的部分
        # print(symbol_folder)

        symbol_folder_path = os.path.join(main_folder_path, symbol_folder)

        # print(symbol_folder_path)

        with open(symbol_folder_path, "r") as file:
            symbol_values = json.load(file)
        ma_2_value = 1

        for d in symbol_values:
            long_value = round(d["netLongsClose"] / (ma_data[symbol_name]["l"] * ma_2_value), 1)
            short_value = round(d["netShortsClose"] / (ma_data[symbol_name]["s"] * ma_2_value), 1)
            # symbol_data[d["begin"]] = {f"{symbol_name}_l":long_value, f"{symbol_name}_s":short_value}
            # 更新 value_data
            timestamp = d["begin"]
            if timestamp not in value_data:
                value_data[timestamp] = {}
            value_data[timestamp].update({
                f"{symbol_name}_l": long_value,
                f"{symbol_name}_s": short_value
            })

    # 将 value_data 写入 value_data.json 文件
    # output_file_path = os.path.join(main_folder_path, "value_data.json")
    with open("data/value_all.json", "w", encoding="utf-8") as output_file:
        json.dump(value_data, output_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main_path = "long_short"
    new_all_path = "long_short_all"
    process_long_short_data(main_path, new_all_path)
    long_short_ma_json(new_all_path)
    long_short_value(new_all_path)
