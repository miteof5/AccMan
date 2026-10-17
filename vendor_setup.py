# -*- coding: utf-8 -*-
"""vendor 依赖引导：任何模块在使用第三方库前先 import 本模块。

pywin32 的 win32api 等 C 扩展位于 vendor\\win32 子目录，
只能通过 site.addsitedir() 处理 vendor 下的 .pth 文件才能被找到。
"""
import os
import site
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(BASE, "vendor")

if os.path.isdir(VENDOR):
    site.addsitedir(VENDOR)
    if VENDOR not in sys.path:
        sys.path.insert(0, VENDOR)
