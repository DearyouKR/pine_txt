import os
import json
from datetime import datetime, timezone, timedelta

def list_json_files(folder_path):
    """
    获取指定文件夹中的所有 JSON 文件，并打印文件名。

    参数：
        folder_path (str): 文件夹路径
    """
    try:
        # 确保路径存在并是文件夹
        if not os.path.exists(folder_path):
            print(f"路径不存在: {folder_path}")
            return
        if not os.path.isdir(folder_path):
            print(f"路径不是一个文件夹: {folder_path}")
            return

        # 获取文件夹中所有 JSON 文件
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

        # 打印每个文件名（不包括扩展名）并循环打开文件
        for json_file in json_files:
            file_name = os.path.splitext(json_file)[0]
            print(file_name)

            # 构建文件的完整路径
            file_path = os.path.join(folder_path, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)  # 读取 JSON 文件内容
                    # print(f"内容: {data}")  # 打印文件内容（可根据需求修改）
            except Exception as e:
                print(f"无法读取文件 {json_file}: {e}")


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
                new_file_path = os.path.join(f"long_short/{file_name}/", f"{date_str}.json")
                print(new_file_path)

                # 检查文件是否存在
                if os.path.exists(new_file_path):
                    # 如果文件存在，加载现有数据
                    with open(new_file_path, "r", encoding="utf-8") as f:
                        existing_records = json.load(f)

                    # 使用字典以 "begin" 为键，合并去重
                    combined_records = {record["begin"]: record for record in (existing_records + records)}
                    # 转换回列表进行保存
                    records = list(combined_records.values())

                # 保存数据到文件
                with open(new_file_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=4)

                print(f"文件 {file_path} 已写入，记录数: {len(records)}")
                #

    except Exception as e:
        print(f"发生错误: {e}")


# 示例使用
folder_path = "15_18"  # 替换为你的实际文件夹路径
list_json_files(folder_path)
