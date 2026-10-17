# -*- coding: utf-8 -*-
"""运行路径分离：只读资源 vs 可写数据。

- resource_dir()：config.json、assets/ 等程序资源。打包后在 PyInstaller 临时目录 _MEIPASS。
- data_dir()：accounts.enc 等用户数据。打包后在 exe 同目录，方便备份/换机。
开发时两者都是脚本目录，行为不变。
"""
import os
import sys


def resource_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def data_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
