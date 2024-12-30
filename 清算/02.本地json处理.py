import os
import json
from datetime import datetime, timedelta


def process_long_short_data(main_folder_path, all_path):
    # 获取当前时间
    current_time = datetime.now()
    # 最近7天的时间戳范围
    recent_seven_days_start = int((current_time - timedelta(days=10)).timestamp())

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
                            print(f"{file_path}:{len(data)}")
                            all_data.extend(data)  # 将数据追加到all_data中
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON from file: {file_path}")

        # 对数据按t字段从小到大排序
        all_data.sort(key=lambda x: x.get('t', 0))

        # 筛选最近7日的数据
        recent_data = [item for item in all_data if item.get('t', 0) >= recent_seven_days_start]

        # 写入到子文件夹目录下的all.json文件
        output_file_path = os.path.join(all_path, f"{symbol_folder}_all.json")
        # print(f"output_file_path: {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(recent_data, output_file, indent=4, ensure_ascii=False)


def long_short_value(main_folder_path):
    with open("data/ma_values.json", 'r', encoding='utf-8') as file:
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
            long_value = round(d["l"] / (ma_data[symbol_name]["l"] * ma_2_value), 1)
            short_value = round(d["s"] / (ma_data[symbol_name]["s"] * ma_2_value), 1)
            # symbol_data[d["t"]] = {f"{symbol_name}_l":long_value, f"{symbol_name}_s":short_value}
            # 更新 value_data
            timestamp = d["t"]
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
    main_path = "liquidation"
    new_all_path = "liquidation_all"
    process_long_short_data(main_path, new_all_path)
    long_short_value(new_all_path)
