# -*- coding: utf-8 -*-
"""账号存储：整个数据文件用 DPAPI 加密后落盘，账号/密码均不出现明文。

数据文件 accounts.enc 结构：DPAPI(JSON)
JSON 内容为列表：[{"remark": "舰长昵称", "username": "邮箱/手机号", "password": "密码"}, ...]
"""
import json
import os
import threading
from datetime import datetime

from credentials import protect, unprotect
from paths import data_dir

DATA_FILE = os.path.join(data_dir(), "accounts.enc")


class AccountStore:
    """线程安全的账号仓库。"""

    def __init__(self, path: str = DATA_FILE):
        self.path = path
        self._lock = threading.Lock()
        self._accounts: list = []
        self.load()

    def load(self):
        with self._lock:
            if os.path.exists(self.path):
                try:
                    with open(self.path, "rb") as f:
                        cipher = f.read()
                    plain = unprotect(cipher)
                    data = json.loads(plain)
                    self._accounts = [
                        {"remark": str(a.get("remark", "")),
                         "username": str(a.get("username", "")),
                         "password": str(a.get("password", "")),
                         "last_used": a.get("last_used")}
                        for a in data
                    ]
                    return
                except Exception:
                    # 文件损坏 / 换过系统账户：不覆盖原文件，仅以空列表启动
                    self._accounts = []
                    return
            self._accounts = []

    def save(self):
        with self._lock:
            plain = json.dumps(self._accounts, ensure_ascii=False, indent=2)
            with open(self.path, "wb") as f:
                f.write(protect(plain, "genshin-account-helper"))

    def all(self) -> list:
        with self._lock:
            return [dict(a) for a in self._accounts]

    def get(self, index: int) -> dict:
        with self._lock:
            return dict(self._accounts[index])

    def add(self, remark: str, username: str, password: str):
        with self._lock:
            self._accounts.append(
                {"remark": remark.strip(), "username": username.strip(),
                 "password": password, "last_used": None}
            )
        self.save()

    def touch(self, index: int):
        """记录该账号刚刚被使用过（填入成功后调用）。"""
        with self._lock:
            self._accounts[index]["last_used"] = datetime.now().isoformat(timespec="seconds")
        self.save()

    def update(self, index: int, remark: str, username: str, password: str):
        with self._lock:
            self._accounts[index] = {
                "remark": remark.strip(), "username": username.strip(),
                "password": password, "last_used": self._accounts[index].get("last_used")
            }
        self.save()

    def remove(self, index: int):
        with self._lock:
            del self._accounts[index]
        self.save()

    def __len__(self) -> int:
        with self._lock:
            return len(self._accounts)
