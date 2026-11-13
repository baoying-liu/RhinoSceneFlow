"""Windows CurrentUser DPAPI vault. Never print returned credentials.

Import load_credentials() only inside the synthesis process. Running this module
prints metadata only; it does not decrypt or contact a remote service.
"""
import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path

ENDPOINTS = {
    "beijing": "https://dashscope.aliyuncs.com",
    "singapore": "https://dashscope-intl.aliyuncs.com",
}


def vault_path():
    return Path(os.environ["LOCALAPPDATA"]) / "RhinoSceneFlow/credentials/qwen.json"


def metadata():
    path = vault_path()
    if not path.exists():
        return {"configured": False}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("region") not in ENDPOINTS or data.get("version") != 1:
        raise ValueError("Unsupported Qwen credential configuration")
    return {"configured": True, "region": data["region"], "protection": "Windows CurrentUser DPAPI"}


def load_credentials():
    if os.name != "nt":
        raise RuntimeError("This credential vault requires Windows")
    metadata()
    data = json.loads(vault_path().read_text(encoding="utf-8-sig"))
    encrypted = base64.b64decode(data["protectedKey"], validate=True)

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = (ctypes.c_ubyte * len(encrypted)).from_buffer_copy(encrypted)
    source = Blob(len(encrypted), buffer)
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.restype = wintypes.BOOL
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    if not crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise RuntimeError("Cannot decrypt Qwen credential for this Windows user")
    try:
        key = ctypes.string_at(target.data, target.size).decode("utf8")
    finally:
        ctypes.memset(target.data, 0, target.size)
        kernel.LocalFree(target.data)
    return {"api_key": key, "region": data["region"], "base_url": ENDPOINTS[data["region"]]}


if __name__ == "__main__":
    try:
        print(json.dumps(metadata()))
    except Exception:
        print(json.dumps({"configured": False, "error": "Credential metadata could not be read"}))
