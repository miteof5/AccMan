# -*- coding: utf-8 -*-
"""原神舰长账号管家 —— 图形界面（CustomTkinter，210px 窄白窗，按 HTML 原型定稿）。

交互：
  - 点账号卡片 = 自动填入原神登录框（半自动，登录按钮自己点）
  - 双击卡片 = 编辑该账号
  - 卡片右侧 ✕ = 删除账号
  - 底部金色按钮 = 添加新账号
"""
import ctypes
import threading
from datetime import datetime

import vendor_setup  # noqa: F401  必须先加载 vendor 依赖

import customtkinter as ctk
from tkinter import messagebox

from accounts import AccountStore
import login_fill

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

FONT = "Microsoft YaHei UI"
GOLD = "#C9A86A"
GOLD_HOVER = "#B8944F"
CARD_BG = "#F7F8FA"
TEXT_MAIN = "#222633"
TEXT_SUB = "#9AA1B0"


def mask_username(u: str) -> str:
    """账号打码：156******74 / a***@xx.com 风格。"""
    u = u.strip()
    if u.isdigit() and len(u) >= 7:
        return u[:3] + "*" * (len(u) - 5) + u[-2:]
    if "@" in u:
        name, domain = u.split("@", 1)
        if len(name) <= 2:
            return name[0] + "***@" + domain
        return name[0] + "***" + name[-1] + "@" + domain
    if len(u) <= 4:
        return u[:1] + "***"
    return u[:2] + "***" + u[-2:]


def fmt_relative(iso: str | None) -> str:
    if not iso:
        return "从未使用"
    try:
        dt = datetime.fromisoformat(iso)
    except Exception:
        return "未知"
    seconds = int((datetime.now() - dt).total_seconds())
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60}分钟前"
    if seconds < 86400:
        return f"{seconds // 3600}小时前"
    if seconds < 86400 * 30:
        return f"{seconds // 86400}天前"
    return dt.strftime("%Y-%m-%d")


class AccountCard(ctk.CTkFrame):
    """一张账号卡片：打码账号粗体 + 备注·时间副行 + ✕ 删除（无头像）。"""

    def __init__(self, master, store, index, on_refresh, on_status):
        super().__init__(master, corner_radius=9, fg_color=CARD_BG)
        self.store = store
        self.index = index
        self.on_refresh = on_refresh
        self.on_status = on_status

        acc = store.get(index)

        self.lbl_account = ctk.CTkLabel(
            self, text=mask_username(acc["username"]),
            font=(FONT, 13, "bold"), anchor="w", text_color=TEXT_MAIN)
        self.lbl_account.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))

        sub = (f"{acc['remark']} · " if acc["remark"] else "") + fmt_relative(acc["last_used"])
        self.lbl_time = ctk.CTkLabel(
            self, text=sub, font=(FONT, 10), anchor="w", text_color=TEXT_SUB)
        self.lbl_time.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))

        btn = ctk.CTkButton(
            self, text="✕", width=20, height=20, corner_radius=10,
            fg_color="transparent", text_color="#C8CDD8", hover_color="#FFEDED",
            font=(FONT, 9), command=self._delete)
        btn.grid(row=0, column=1, rowspan=2, padx=(0, 6))

        self.columnconfigure(0, weight=1)

        # 单击卡片任意处 = 填入；双击 = 编辑
        for w in (self, self.lbl_account, self.lbl_time):
            w.bind("<Button-1>", lambda e: self._fill())
            w.bind("<Double-Button-1>", lambda e: self._edit())

    def _fill(self):
        acc = self.store.get(self.index)
        self.on_status(f"正在把【{acc['remark'] or mask_username(acc['username'])}】送入登录框 ...")
        threading.Thread(target=self._worker, args=(acc,), daemon=True).start()

    def _worker(self, acc):
        try:
            msg = login_fill.fill_into_genshin(acc["username"], acc["password"])
            self.store.touch(self.index)  # 记录本次使用时间
            self.after(0, lambda: (self.on_status(msg), self.on_refresh()))
        except Exception as e:
            self.after(0, lambda: self.on_status(f"填入失败：{e}"))

    def _edit(self):
        acc = self.store.get(self.index)
        dialog = AccountDialog(self, self.store, self.index, acc["remark"], acc["username"])
        self.wait_window(dialog)
        self.on_refresh()

    def _delete(self):
        acc = self.store.get(self.index)
        name = acc["remark"] or mask_username(acc["username"])
        if messagebox.askyesno("删除账号", f"确定删除「{name}」吗？", parent=self):
            self.store.remove(self.index)
            self.on_refresh()
            self.on_status("已删除账号。")


class AccountDialog(ctk.CTkToplevel):
    """添加/编辑账号对话框（按原型：标题 + 三输入框 + 取消/保存并排）。"""

    def __init__(self, master, store, index=None, remark="", username=""):
        super().__init__(master)
        self.store = store
        self.index = index
        self.title("编辑账号" if index is not None else "添加账号")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # 位置绑定主窗口：居中叠在主窗口上
        master.update_idletasks()
        mx, my = master.winfo_x(), master.winfo_y()
        mw, mh = master.winfo_width(), master.winfo_height()
        self.geometry(f"240x210+{mx + (mw - 240) // 2}+{my + (mh - 210) // 2}")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(body, text="添加账号" if index is None else "编辑账号",
                     anchor="w", font=(FONT, 14, "bold"), text_color=TEXT_MAIN).pack(fill="x", pady=(0, 8))

        self.username_entry = ctk.CTkEntry(body, placeholder_text="手机号 / 邮箱",
                     font=(FONT, 11), height=26, border_width=1, border_color="#E4E7EE")
        self.username_entry.pack(fill="x", pady=3)
        if username:
            self.username_entry.insert(0, username)

        self.password_entry = ctk.CTkEntry(body, placeholder_text="密码", show="*",
                     font=(FONT, 11), height=26, border_width=1, border_color="#E4E7EE")
        self.password_entry.pack(fill="x", pady=3)

        self.remark_entry = ctk.CTkEntry(body, placeholder_text="备注（选填，如舰长昵称）",
                     font=(FONT, 11), height=26, border_width=1, border_color="#E4E7EE")
        self.remark_entry.pack(fill="x", pady=3)
        if remark:
            self.remark_entry.insert(0, remark)

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(btns, text="取消", width=80, height=26, corner_radius=6,
                      fg_color="#F2F3F7", text_color="#555555", hover_color="#E5E7EE",
                      font=(FONT, 11), command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(btns, text="保存", width=80, height=26, corner_radius=6,
                      fg_color=GOLD, hover_color=GOLD_HOVER,
                      font=(FONT, 11), command=self._save).pack(side="left", expand=True, fill="x", padx=(4, 0))

    def _save(self):
        remark = self.remark_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("提示", "账号和密码不能为空。", parent=self)
            return
        if self.index is not None:
            self.store.update(self.index, remark, username, password)
        else:
            self.store.add(remark, username, password)
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("账号管理器")
        try:
            import os
            from paths import resource_dir
            self.iconbitmap(os.path.join(resource_dir(), "assets", "icon.ico"))
        except Exception:
            pass
        self.geometry("280x360")
        self.minsize(240, 280)
        # 初始打开居中屏幕
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"280x360+{(sw - 280) // 2}+{(sh - 360) // 2}")
        self.store = AccountStore()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="舰长账号", font=(FONT, 16, "bold"), text_color=TEXT_MAIN).grid(
            row=0, column=0, sticky="w")
        self.search_entry = ctk.CTkEntry(top, placeholder_text="搜索账号", width=78,
                              font=(FONT, 11), height=22,
                              border_width=1, border_color="#E4E7EE")
        self.search_entry._entry.configure(insertwidth=1)
        self.search_entry.grid(row=0, column=1, sticky="e")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color="#C8CDD8",
            scrollbar_button_hover_color="#A9B0BE")
        self.list_frame._scrollbar.configure(width=4)
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.list_frame.grid_columnconfigure(0, weight=1)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 20))
        ctk.CTkButton(bottom, text="＋ 添加账号", corner_radius=8, height=28,
                      fg_color=GOLD, hover_color=GOLD_HOVER,
                      font=(FONT, 12), command=self.add_account).pack(fill="x")

        self.status_var = ctk.StringVar(value="")
        self.status_label = ctk.CTkLabel(self, textvariable=self.status_var, text_color=TEXT_SUB,
                      font=(FONT, 10))
        self.status_label.grid(row=3, column=0, sticky="w", padx=14, pady=(0, 0))
        self.status_label.grid_remove()

    def add_account(self):
        dialog = AccountDialog(self, self.store)
        self.wait_window(dialog)
        self.refresh()

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        kw = self.search_entry.get().strip().lower()
        indexes = []
        for i in range(len(self.store)):
            acc = self.store.get(i)
            hay = f"{acc['remark']} {acc['username']}".lower()
            if not kw or kw in hay:
                indexes.append(i)
        if not indexes:
            ctk.CTkLabel(
                self.list_frame, text="（点底部按钮添加账号）",
                text_color=TEXT_SUB, font=(FONT, 10)).pack(pady=20)
            return
        for i in indexes:
            AccountCard(self.list_frame, self.store, i, self.refresh, self.set_status).pack(
                fill="x", pady=3)
        self.after(60, self._fit_scrollbar)

    def _fit_scrollbar(self):
        """内容不超出可视区时隐藏滚动条，超出时才显示。"""
        try:
            sb = self.list_frame._scrollbar
            inner = self.list_frame.winfo_children()
            content_h = sum(w.winfo_reqheight() + 6 for w in inner)  # pady=3 上下各 3
            if content_h <= self.list_frame.winfo_height():
                sb.grid_remove()
            else:
                sb.grid()
        except Exception:
            pass

    def set_status(self, msg):
        self.status_var.set(msg)
        if msg:
            self.status_label.grid()
        else:
            self.status_label.grid_remove()


if __name__ == "__main__":
    app = App()
    app.mainloop()
