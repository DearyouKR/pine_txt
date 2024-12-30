@echo off
REM 激活 Conda 的 base 环境
CALL conda activate base

REM 切换到脚本所在目录
cd /d D:\06.编程\01.python\01.交易\pine_get

REM 运行 Python 脚本
python main.py

REM 保持窗口打开（可选）
pause
