# -*- coding: utf-8 -*-
"""Windows DPAPI 加密/解密。

通过 ctypes 直接调用系统 crypt32.dll，不依赖任何第三方库。
加密结果绑定当前 Windows 用户账户：只有本机当前用户能解密，
其他账户、其他程序读走密文也解不开。
"""
import ctypes
import ctypes.wintypes

_LOCAL_FREE = ctypes.windll.kernel32.LocalFree
_CRYPT_PROTECT = ctypes.windll.crypt32.CryptProtectData
_CRYPT_UNPROTECT = ctypes.windll.crypt32.CryptUnprotectData


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _make_blob(data: bytes) -> _DATA_BLOB:
    buf = ctypes.create_string_buffer(data, len(data))
    return _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))


def _blob_to_bytes(blob: _DATA_BLOB) -> bytes:
    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        if blob.pbData:
            _LOCAL_FREE(blob.pbData)


def protect(plaintext: str, description: str = "genshin-account-helper") -> bytes:
    """加密 UTF-8 字符串，返回密文 bytes。"""
    data = plaintext.encode("utf-8")
    in_blob = _make_blob(data)
    out_blob = _DATA_BLOB()
    if not _CRYPT_PROTECT(
        ctypes.byref(in_blob), description, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise ctypes.WinError()
    return _blob_to_bytes(out_blob)


def unprotect(ciphertext: bytes) -> str:
    """解密 bytes，返回 UTF-8 字符串。"""
    in_blob = _make_blob(ciphertext)
    out_blob = _DATA_BLOB()
    if not _CRYPT_UNPROTECT(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise ctypes.WinError()
    return _blob_to_bytes(out_blob).decode("utf-8")
