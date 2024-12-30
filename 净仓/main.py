import schedule
import time
import subprocess

main_path = "/root/coinank/main/"
log_file_path = f"{main_path}data/coinank.log"

# 在程序启动时清空日志文件
with open(log_file_path, "w") as log_file:
    log_file.write("")

def run_15m():
    with open(log_file_path, "a") as log_file:
        subprocess.call(["python", f"{main_path}/long_short_minus.py"], stdout=log_file, stderr=log_file)

# 定时任务安排
schedule.every().hour.at(":01").do(run_15m)
schedule.every().hour.at(":16").do(run_15m)
schedule.every().hour.at(":31").do(run_15m)
schedule.every().hour.at(":46").do(run_15m)

# 循环检测是否到达指定时间
while True:
    schedule.run_pending()
    time.sleep(1)
