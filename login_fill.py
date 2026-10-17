# -*- coding: utf-8 -*-
"""半自动填入：把账号密码依次送进原神登录框。

流程：激活原神窗口 -> 全屏截图 -> 模板匹配 miHoYo 标志定位登录卡片
     -> 按偏移算出账号框/密码框 -> 剪贴板粘贴账号、密码。
登录按钮由用户手动点（半自动，降低风控风险）。
"""
from __future__ import annotations

import json
import os
import time

import vendor_setup  # noqa: F401
from paths import resource_dir

BASE = resource_dir()
with open(os.path.join(BASE, "config.json"), encoding="utf-8") as f:
    CFG = json.load(f)


def _activate_genshin() -> bool:
    """把原神窗口拉到前台。"""
    import pygetwindow as gw
    title = CFG["window_title"]
    wins = [w for w in gw.getAllWindows() if title in (w.title or "")]
    if not wins:
        return False
    w = wins[0]
    try:
        if w.isMinimized:
            w.restore()
        w.activate()
    except Exception:
        pass
    time.sleep(0.7)
    return True


def _find_logo() -> tuple:
    """全屏截图找 miHoYo 标志，返回 (logo左上角屏幕坐标, 置信度)。"""
    import cv2
    import numpy as np
    from mss import mss

    template = cv2.imread(os.path.join(BASE, CFG["template"]))
    if template is None:
        raise RuntimeError("模板图片缺失：" + CFG["template"])
    with mss() as sct:
        mon = sct.monitors[1]  # 主显示器
        shot = np.array(sct.grab(mon))
    shot_bgr = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)
    res = cv2.matchTemplate(shot_bgr, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < CFG["threshold"]:
        return None, float(max_val)
    return (mon["left"] + max_loc[0], mon["top"] + max_loc[1]), float(max_val)


def fill_into_genshin(username: str, password: str) -> str:
    """把账号密码填入原神登录框，返回提示语。"""
    import pyautogui
    import pyperclip

    if not _activate_genshin():
        raise RuntimeError("没找到原神窗口，请先打开原神客户端到登录界面")

    logo_pos, score = _find_logo()
    if logo_pos is None:
        raise RuntimeError(
            f"没在屏幕上找到登录界面（置信度 {score:.2f}）。"
            "请确认原神窗口已打开、停在账号密码登录界面。"
        )

    lx, ly = logo_pos
    ox1, oy1 = CFG["offsets"]["field1"]
    ox2, oy2 = CFG["offsets"]["field2"]

    # 账号框：点击 -> 全选清空 -> 粘贴
    pyperclip.copy(username)
    pyautogui.click(lx + ox1, ly + oy1)
    time.sleep(0.25)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.25)

    # 密码框：点击 -> 全选清空 -> 粘贴
    pyperclip.copy(password)
    pyautogui.click(lx + ox2, ly + oy2)
    time.sleep(0.25)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "v")

    # 清空剪贴板，避免明文密码留在剪贴板里
    pyperclip.copy("")
    return ""
