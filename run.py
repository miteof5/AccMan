# -*- coding: utf-8 -*-
"""原神舰长账号管家 —— 启动容错：报错写 error.log 并弹窗，不闪退。"""
import os
import traceback
import tkinter as tk
from tkinter import messagebox

import vendor_setup  # noqa: F401  必须先加载 vendor 依赖

BASE = os.path.dirname(os.path.abspath(__file__))


def _show_fatal(err: str):
    try:
        with open(os.path.join(BASE, "error.log"), "w", encoding="utf-8") as f:
            f.write(err)
    except Exception:
        pass
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("原神舰长账号管家 - 启动失败", err[-2000:])
        root.destroy()
    except Exception:
        pass


def main():
    from main import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _show_fatal(traceback.format_exc())
        raise
