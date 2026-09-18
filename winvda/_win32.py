"""Low-level Win32 and COM interop bindings via standard library ctypes."""

import ctypes
from ctypes import byref, c_long, c_ulong, c_void_p, wintypes
import sys
from typing import Any, Optional, Tuple
import uuid

from winvda.errors import ShellUnavailableError, VdaComError

HRESULT = c_long

# COM apartment flags
COINIT_MULTITHREADED = 0x0
COINIT_APARTMENTTHREADED = 0x2
COINIT_DISABLE_OLE1DDE = 0x4

# COM execution contexts
CLSCTX_INPROC_SERVER = 0x1
CLSCTX_LOCAL_SERVER = 0x4

# HRESULT Constants
S_OK = 0x00000000
S_FALSE = 0x00000001
E_NOTIMPL = 0x80004001
E_NOINTERFACE = 0x80004002
E_POINTER = 0x80004003
E_FAIL = 0x80004005
E_ACCESSDENIED = 0x80070005
E_ELEMENTNOTFOUND = 0x80070490
REGDB_E_CLASSNOTREG = 0x80040154
CO_E_SERVER_EXEC_FAILURE = 0x80080005
RPC_E_DISCONNECTED = 0x80010108
RPC_E_WRONG_THREAD = 0x8001010E
RPC_S_SERVER_UNAVAILABLE = 0x800706BA

# Shell unavailable error set
SHELL_UNAVAILABLE_HRESULTS = {
    RPC_S_SERVER_UNAVAILABLE,
    RPC_E_DISCONNECTED,
    CO_E_SERVER_EXEC_FAILURE,
    REGDB_E_CLASSNOTREG,
}

# Native DLL loads
ole32 = ctypes.windll.ole32
user32 = ctypes.windll.user32
combase = getattr(ctypes.windll, "combase", ole32)

# Windows Runtime String APIs
_WindowsGetStringRawBuffer = getattr(combase, "WindowsGetStringRawBuffer", None)
if _WindowsGetStringRawBuffer:
    _WindowsGetStringRawBuffer.restype = wintypes.LPCWSTR
    _WindowsGetStringRawBuffer.argtypes = [c_void_p, ctypes.POINTER(wintypes.UINT)]

_WindowsDeleteString = getattr(combase, "WindowsDeleteString", None)
if _WindowsDeleteString:
    _WindowsDeleteString.restype = HRESULT
    _WindowsDeleteString.argtypes = [c_void_p]

_WindowsCreateString = getattr(combase, "WindowsCreateString", None)
if _WindowsCreateString:
    _WindowsCreateString.restype = HRESULT
    _WindowsCreateString.argtypes = [wintypes.LPCWSTR, wintypes.UINT, ctypes.POINTER(c_void_p)]


class GUID(ctypes.Structure):
    """Win32 GUID representation."""
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


def py_uuid_to_guid(u: uuid.UUID) -> GUID:
    """Convert Python UUID to ctypes GUID."""
    fields = u.fields
    data4 = (wintypes.BYTE * 8)(*u.bytes[8:])
    return GUID(fields[0], fields[1], fields[2], data4)


def guid_to_py_uuid(g: GUID) -> uuid.UUID:
    """Convert ctypes GUID to Python UUID."""
    return uuid.UUID(bytes_le=bytes(g))


def check_hresult(hr: int, context: Optional[str] = None) -> None:
    """Validate COM HRESULT and raise appropriate library exceptions."""
    if hr >= 0:
        return
    unsigned_hr = hr & 0xFFFFFFFF
    if unsigned_hr in SHELL_UNAVAILABLE_HRESULTS:
        raise ShellUnavailableError(unsigned_hr, "Windows Shell (explorer.exe) is unavailable or restarting", context)
    raise VdaComError(unsigned_hr, "COM call returned error", context)


def call_vtable(ptr: c_void_p, slot: int, restype: Any, argtypes: list, *args: Any) -> Any:
    """Execute a virtual method table slot dispatch on a COM interface pointer."""
    if not ptr:
        raise VdaComError(E_POINTER, "Attempted vtable call on null interface pointer")
    vtable = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(c_void_p))).contents
    func_ptr = vtable[slot]
    proto = ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)
    func = proto(func_ptr)
    return func(ptr, *args)


def safe_release(ptr: Optional[c_void_p]) -> None:
    """Release an IUnknown interface pointer safely (Slot 2).

    Destructors and cleanup routines in COM must be non-throwing (noexcept).
    If the remote server (explorer.exe) terminated during execution, invoking
    Release on a dead RPC proxy raises an RPC communication failure. We
    explicitly suppress RPC/COM transport errors during teardown to avoid
    masking the primary exception in caller finally blocks.
    """
    if ptr and getattr(ptr, "value", None):
        try:
            call_vtable(ptr, 2, wintypes.ULONG, [])
        except (OSError, VdaError):
            pass


def read_hstring(hstr: c_void_p) -> str:
    """Read a Windows HSTRING into a Python str and free the handle."""
    if not hstr or not _WindowsGetStringRawBuffer:
        return ""
    length = wintypes.UINT()
    raw = _WindowsGetStringRawBuffer(hstr, byref(length))
    val = raw if raw else ""
    if _WindowsDeleteString:
        _WindowsDeleteString(hstr)
    return val


def create_hstring(text: str) -> c_void_p:
    """Create a Windows HSTRING from a Python str."""
    if not _WindowsCreateString:
        return c_void_p()
    out_hstr = c_void_p()
    hr = _WindowsCreateString(text, len(text), byref(out_hstr))
    check_hresult(hr, "WindowsCreateString")
    return out_hstr


def get_window_title(hwnd: int) -> str:
    """Retrieve window title text via Win32 GetWindowTextW."""
    if not user32.IsWindow(hwnd):
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


# Foreground window API
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetForegroundWindow.argtypes = []


def get_foreground_window() -> int:
    """Retrieve handle to active foreground window via Win32 GetForegroundWindow."""
    return user32.GetForegroundWindow()

