import pprint
import json
import subprocess
import os
import time


def pine_txt(data_list):
    data_len = len(data_list)

    len_start = 0

    txt = ""
    first = True  # Track if we're on the first iteration
    for data in data_list:
        if first:
            cleaned_data = data.lstrip()  # Remove leading spaces from the first data
            txt += f"{cleaned_data}\n"  # No newline for the first data
            first = False  # Set first to False after the first iteration
        elif len_start == data_len - 1:
            txt += f"{data}"
        else:
            txt += f"{data}\n"  # Keep the rest as is

        len_start += 1

    return txt


def update_data_from_pine(data_file, pine_file, output_file):
    # 读取 data.txt 文件内容
    with open(data_file, "r", encoding="utf-8") as file:
        data = file.read()

    # 读取 pine.json 文件内容
    with open(pine_file, "r", encoding="utf-8") as f:
        pine_data = json.load(f)

    # 替换占位符
    for key, value in pine_data.items():
        placeholder = f"{{{{{key}}}}}"  # 构造占位符，如 {{long_key}}
        txt = pine_txt(value)
        data = data.replace(placeholder, str(txt))

    # 写入更新后的文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(data)

    print(f"更新后的数据已保存到 {output_file}")


# def run_python_script(script_path):
#     # 检查文件是否存在
#     if not os.path.isfile(script_path):
#         print(f"文件路径无效: {script_path}")
#         return
#
#     # 检查文件扩展名是否为 .py
#     if not script_path.endswith('.py'):
#         print("文件不是一个 Python 脚本: {script_path}")
#         return
#
#     try:
#         # 使用 subprocess.run 执行 Python 脚本
#         result = subprocess.run(['python', script_path], capture_output=True, text=True, encoding='utf-8')
#
#         # 打印脚本的输出
#         print("脚本输出:")
#         print(result.stdout)
#
#         # 如果有错误输出，打印错误信息
#         if result.stderr:
#             print("脚本错误:")
#             print(result.stderr)
#     except Exception as e:
#         print(f"运行脚本时发生错误: {e}")


def run_python_script(script_path):
    # 检查文件是否存在
    if not os.path.isfile(script_path):
        print(f"文件路径无效: {script_path}")
        return

    # 检查文件扩展名是否为 .py
    if not script_path.endswith('.py'):
        print(f"文件不是一个 Python 脚本: {script_path}")
        return

    # 获取脚本所在的目录和文件名
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # 记录当前工作目录
    original_cwd = os.getcwd()

    try:
        # 切换到脚本所在目录
        if script_dir:
            os.chdir(script_dir)

        # 使用 subprocess.run 执行 Python 脚本
        result = subprocess.run(['python', script_name], capture_output=True, text=True, encoding='utf-8',
                                errors='replace')

        print("脚本输出:")
        print(result.stdout)

        if result.stderr:
            print("脚本错误:")
            print(result.stderr)
    except Exception as e:
        print(f"运行脚本时发生错误: {e}")
    finally:
        # 恢复原来的工作目录
        os.chdir(original_cwd)


if __name__ == "__main__":
    start_time_a = time.time()

    # run_python_script("净仓/01.服务器文件下载.py")
    # # run_python_script("净仓/04.增加数据.py")
    # run_python_script("净仓/05.本地json文件处理新版.py")
    # run_python_script("净仓/03.pine_生成.py")
    # run_python_script("清算/01.服务器文件下载.py")
    # run_python_script("清算/02.本地json处理.py")
    # run_python_script("清算/03.pine_生成.py")

    # 使用示例
    data_file = 'pine.txt'
    pine_file = 'pine_dict.json'
    output_file = 'updated_data.txt'  # 输出的新文件

    update_data_from_pine(data_file, pine_file, output_file)

    end_time_a = time.time()  # 记录脚本结束时间
    run_time = end_time_a - start_time_a  # 计算脚本运行时间
    print(f"run_time：{int(run_time / 60)} M {int(run_time % 60)} S")
