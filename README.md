# AccMan · 原神账号管理器

多个米哈游通行证账号之间快速切换：自动把账号密码填入原神登录框，你手动点「进入游戏」。

## 使用

- 免安装：下载 `dist/accman.exe`，双击运行
- 点「＋ 添加账号」录入账号 → 打开原神到登录界面 → 点卡片自动填入
- 密码本地 DPAPI 加密（绑定你的 Windows 账户，拷走文件也解不开）

## 从源码运行

```bash
pip install -r requirements.txt
python run.py
```

## 说明

- 半自动：只填账号密码，登录和滑块手动完成，行为与真人一致
- 坐标适配 1920×1080，分辨率不同时调 `config.json` 里的 offsets
- 账号数据 `accounts.enc` 在 exe 同目录，备份直接拷它
