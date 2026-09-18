"""Window and multi-window application pinning with native Task View parity.

This module resolves the sub-AUMID isolation defect where applications hosted
inside XAML Islands or detached frames (such as Windows Terminal or modern IDEs)
receive per-window identifiers (~Wh~w<HEX_HWND>).

It implements the native Task View execution path discovered in twinui.pcshell.dll:
1. Canonical base package registration in IVirtualDesktopPinnedApps::PinAppID.
2. Individual sub-view pinning via IVirtualDesktopPinnedApps::PinView.
3. Desktop switch synchronization via sync_pinned_apps().
"""

from contextlib import contextmanager
import ctypes
from ctypes import byref, c_void_p, wintypes
from typing import Generator, List, Optional, Tuple
from uuid import UUID

from winvda._win32 import (
    CLSCTX_LOCAL_SERVER,
    COINIT_MULTITHREADED,
    GUID,
    HRESULT,
    call_vtable,
    check_hresult,
    get_window_title,
    guid_to_py_uuid,
    ole32,
    safe_release,
    user32,
)
from winvda._vtables import (
    CLSID_ImmersiveShell,
    CLSID_VirtualDesktopPinnedApps,
    IID_IApplicationView,
    IID_IApplicationViewCollection,
    IID_IServiceProvider,
    IID_IVirtualDesktopPinnedApps,
)
from winvda.errors import VdaComError, WindowNotFoundError
from winvda.types import WindowView


@contextmanager
def transient_pinning_session() -> Generator[Tuple[c_void_p, c_void_p, c_void_p], None, None]:
    """Call-scoped transient session acquiring IServiceProvider, PinnedApps, and ViewCollection."""
    hr_init = ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
    co_initialized = (hr_init >= 0)

    p_sp = c_void_p()
    p_pinned = c_void_p()
    p_avc = c_void_p()
    try:
        hr_sp = ole32.CoCreateInstance(
            byref(CLSID_ImmersiveShell),
            None,
            CLSCTX_LOCAL_SERVER,
            byref(IID_IServiceProvider),
            byref(p_sp),
        )
        check_hresult(hr_sp, "CoCreateInstance(CLSID_ImmersiveShell)")

        hr_pin = call_vtable(
            p_sp, 3, HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(CLSID_VirtualDesktopPinnedApps),
            byref(IID_IVirtualDesktopPinnedApps),
            byref(p_pinned),
        )
        check_hresult(hr_pin, "QueryService(IVirtualDesktopPinnedApps)")

        hr_avc = call_vtable(
            p_sp, 3, HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(IID_IApplicationViewCollection),
            byref(IID_IApplicationViewCollection),
            byref(p_avc),
        )
        check_hresult(hr_avc, "QueryService(IApplicationViewCollection)")

        yield (p_sp, p_pinned, p_avc)
    finally:
        safe_release(p_avc)
        safe_release(p_pinned)
        safe_release(p_sp)
        if co_initialized:
            ole32.CoUninitialize()


def normalize_base_app_id(app_id: Optional[str]) -> Optional[str]:
    """Strip ~Wh~ sub-AUMID tokens to extract the canonical application package identity."""
    if not app_id:
        return None
    if "~Wh~" in app_id:
        return app_id.split("~Wh~")[0]
    return app_id


def _get_view_properties(
    p_pinned: c_void_p,
    p_view: c_void_p,
    hwnd: int,
) -> WindowView:
    """Extract metadata properties from an active IApplicationView interface pointer."""
    view_vt = ctypes.cast(p_view, ctypes.POINTER(ctypes.POINTER(c_void_p))).contents

    # Slot 17: GetAppUserModelId(out PWSTR)
    aumid_ptr = wintypes.LPWSTR()
    try:
        hr_aumid = call_vtable(
            p_view, 17, HRESULT,
            [ctypes.POINTER(wintypes.LPWSTR)],
            byref(aumid_ptr),
        )
        raw_app_id = aumid_ptr.value if hr_aumid == 0 and aumid_ptr else None
    finally:
        if aumid_ptr:
            ole32.CoTaskMemFree(aumid_ptr)

    base_app_id = normalize_base_app_id(raw_app_id)

    # Slot 24: GetVirtualDesktopId(out GUID)
    vd_guid = GUID()
    hr_vd = call_vtable(
        p_view, 24, HRESULT,
        [ctypes.POINTER(GUID)],
        byref(vd_guid),
    )
    desktop_id = guid_to_py_uuid(vd_guid) if hr_vd == 0 else None

    # Slot 6 on IVirtualDesktopPinnedApps: IsViewPinned
    is_view_pinned = wintypes.BOOL()
    hr_ivp = call_vtable(
        p_pinned, 6, HRESULT,
        [c_void_p, ctypes.POINTER(wintypes.BOOL)],
        p_view, byref(is_view_pinned),
    )
    is_pinned = bool(is_view_pinned.value) if hr_ivp == 0 else False

    # Slot 3 on IVirtualDesktopPinnedApps: IsAppIdPinned
    is_app_pinned = False
    if base_app_id:
        c_is_app = wintypes.BOOL()
        hr_iap = call_vtable(
            p_pinned, 3, HRESULT,
            [wintypes.LPCWSTR, ctypes.POINTER(wintypes.BOOL)],
            base_app_id, byref(c_is_app),
        )
        if hr_iap == 0:
            is_app_pinned = bool(c_is_app.value)

    title = get_window_title(hwnd)

    return WindowView(
        hwnd=hwnd,
        title=title,
        app_id=raw_app_id,
        base_app_id=base_app_id,
        desktop_id=desktop_id,
        is_pinned=is_pinned,
        is_app_pinned=is_app_pinned,
    )


def get_window_view(hwnd: int) -> WindowView:
    """Retrieve the WindowView value object for a specific top-level window handle."""
    if not user32.IsWindow(hwnd):
        raise WindowNotFoundError(f"Invalid or destroyed window handle: {hwnd:#x}")

    with transient_pinning_session() as (p_sp, p_pinned, p_avc):
        p_view = c_void_p()
        hr_gv = call_vtable(
            p_avc, 6, HRESULT,  # GetViewForHwnd
            [wintypes.HWND, ctypes.POINTER(c_void_p)],
            hwnd, byref(p_view),
        )
        if hr_gv != 0 or not p_view:
            raise WindowNotFoundError(f"Window {hwnd:#x} has no managed shell view (HRESULT {hr_gv:#x})")

        try:
            return _get_view_properties(p_pinned, p_view, hwnd)
        finally:
            safe_release(p_view)


def is_window_pinned(hwnd: int) -> bool:
    """Check whether an individual window is pinned to all virtual desktops."""
    return get_window_view(hwnd).is_pinned


def pin_window(hwnd: int) -> None:
    """Pin an individual window to appear on all virtual desktops."""
    if not user32.IsWindow(hwnd):
        raise WindowNotFoundError(f"Invalid window handle: {hwnd:#x}")

    with transient_pinning_session() as (p_sp, p_pinned, p_avc):
        p_view = c_void_p()
        hr_gv = call_vtable(
            p_avc, 6, HRESULT,  # GetViewForHwnd
            [wintypes.HWND, ctypes.POINTER(c_void_p)],
            hwnd, byref(p_view),
        )
        check_hresult(hr_gv, "GetViewForHwnd")
        try:
            hr_pin = call_vtable(
                p_pinned, 7, HRESULT,  # Slot 7: PinView
                [c_void_p],
                p_view,
            )
            check_hresult(hr_pin, "IVirtualDesktopPinnedApps::PinView")
        finally:
            safe_release(p_view)


def unpin_window(hwnd: int) -> None:
    """Unpin an individual window from all virtual desktops."""
    if not user32.IsWindow(hwnd):
        raise WindowNotFoundError(f"Invalid window handle: {hwnd:#x}")

    with transient_pinning_session() as (p_sp, p_pinned, p_avc):
        p_view = c_void_p()
        hr_gv = call_vtable(
            p_avc, 6, HRESULT,  # GetViewForHwnd
            [wintypes.HWND, ctypes.POINTER(c_void_p)],
            hwnd, byref(p_view),
        )
        check_hresult(hr_gv, "GetViewForHwnd")
        try:
            hr_unpin = call_vtable(
                p_pinned, 8, HRESULT,  # Slot 8: UnpinView
                [c_void_p],
                p_view,
            )
            check_hresult(hr_unpin, "IVirtualDesktopPinnedApps::UnpinView")
        finally:
            safe_release(p_view)


def toggle_pin_window(hwnd: int) -> bool:
    """Toggle the pinned state of an individual window. Returns the new pinned state."""
    if is_window_pinned(hwnd):
        unpin_window(hwnd)
        return False
    pin_window(hwnd)
    return True


def is_app_pinned(hwnd: int) -> bool:
    """Check whether the application owning the window is pinned across all desktops."""
    return get_window_view(hwnd).is_app_pinned


def pin_app(hwnd: int) -> None:
    """Pin an entire application and all its current and future windows across all desktops.

    Implements native Task View parity:
    1. Registers canonical base_app_id via PinAppID.
    2. Enumerates all active application views and invokes PinView on each sibling view.
    """
    view_info = get_window_view(hwnd)
    base_id = view_info.base_app_id

    with transient_pinning_session() as (p_sp, p_pinned, p_avc):
        if base_id:
            # 1. Register canonical package identity
            hr_pin = call_vtable(
                p_pinned, 4, HRESULT,  # Slot 4: PinAppID
                [wintypes.LPCWSTR],
                base_id,
            )
            check_hresult(hr_pin, "IVirtualDesktopPinnedApps::PinAppID")

            # 2. Iterate all views by z-order to pin active sibling sub-views
            p_array = c_void_p()
            hr_z = call_vtable(
                p_avc, 4, HRESULT,  # GetViewsByZOrder
                [ctypes.POINTER(c_void_p)],
                byref(p_array),
            )
            if hr_z == 0 and p_array:
                try:
                    total_views = wintypes.UINT()
                    call_vtable(
                        p_array, 3, HRESULT,
                        [ctypes.POINTER(wintypes.UINT)],
                        byref(total_views),
                    )
                    for i in range(total_views.value):
                        p_sub_view = c_void_p()
                        hr_get = call_vtable(
                            p_array, 4, HRESULT,
                            [wintypes.UINT, ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
                            i, byref(IID_IApplicationView), byref(p_sub_view),
                        )
                        if hr_get == 0 and p_sub_view:
                            try:
                                aumid_ptr = wintypes.LPWSTR()
                                hr_id = call_vtable(
                                    p_sub_view, 17, HRESULT,
                                    [ctypes.POINTER(wintypes.LPWSTR)],
                                    byref(aumid_ptr),
                                )
                                sub_raw = aumid_ptr.value if hr_id == 0 and aumid_ptr else None
                                if aumid_ptr:
                                    ole32.CoTaskMemFree(aumid_ptr)
                                if normalize_base_app_id(sub_raw) == base_id:
                                    call_vtable(p_pinned, 7, HRESULT, [c_void_p], p_sub_view)
                            finally:
                                safe_release(p_sub_view)
                finally:
                    safe_release(p_array)
        else:
            # Classic Win32 app without AUMID: fallback to pinning current window view
            pin_window(hwnd)


def unpin_app(hwnd: int) -> None:
    """Unpin an entire application from all virtual desktops."""
    view_info = get_window_view(hwnd)
    base_id = view_info.base_app_id

    with transient_pinning_session() as (p_sp, p_pinned, p_avc):
        if base_id:
            hr_unpin = call_vtable(
                p_pinned, 5, HRESULT,  # Slot 5: UnpinAppID
                [wintypes.LPCWSTR],
                base_id,
            )
            check_hresult(hr_unpin, "IVirtualDesktopPinnedApps::UnpinAppID")

            # Unpin sibling sub-views
            p_array = c_void_p()
            hr_z = call_vtable(
                p_avc, 4, HRESULT,
                [ctypes.POINTER(c_void_p)],
                byref(p_array),
            )
            if hr_z == 0 and p_array:
                try:
                    total_views = wintypes.UINT()
                    call_vtable(p_array, 3, HRESULT, [ctypes.POINTER(wintypes.UINT)], byref(total_views))
                    for i in range(total_views.value):
                        p_sub_view = c_void_p()
                        hr_get = call_vtable(
                            p_array, 4, HRESULT,
                            [wintypes.UINT, ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
                            i, byref(IID_IApplicationView), byref(p_sub_view),
                        )
                        if hr_get == 0 and p_sub_view:
                            try:
                                aumid_ptr = wintypes.LPWSTR()
                                hr_id = call_vtable(
                                    p_sub_view, 17, HRESULT,
                                    [ctypes.POINTER(wintypes.LPWSTR)],
                                    byref(aumid_ptr),
                                )
                                sub_raw = aumid_ptr.value if hr_id == 0 and aumid_ptr else None
                                if aumid_ptr:
                                    ole32.CoTaskMemFree(aumid_ptr)
                                if normalize_base_app_id(sub_raw) == base_id:
                                    call_vtable(p_pinned, 8, HRESULT, [c_void_p], p_sub_view)
                            finally:
                                safe_release(p_sub_view)
                finally:
                    safe_release(p_array)
        else:
            unpin_window(hwnd)


def toggle_pin_app(hwnd: int) -> bool:
    """Toggle the pinned state of an entire application. Returns the new pinned state."""
    if is_app_pinned(hwnd):
        unpin_app(hwnd)
        return False
    pin_app(hwnd)
    return True


def sync_pinned_apps() -> int:
    """Reconcile newly opened secondary windows of pinned applications.

    Returns the count of views that were updated to pinned status.
    """
    synced_count = 0
    with transient_pinning_session() as (p_sp, p_pinned, p_avc):
        p_array = c_void_p()
        hr_z = call_vtable(
            p_avc, 4, HRESULT,
            [ctypes.POINTER(c_void_p)],
            byref(p_array),
        )
        if hr_z != 0 or not p_array:
            return 0

        try:
            total_views = wintypes.UINT()
            call_vtable(p_array, 3, HRESULT, [ctypes.POINTER(wintypes.UINT)], byref(total_views))
            for i in range(total_views.value):
                p_sub_view = c_void_p()
                hr_get = call_vtable(
                    p_array, 4, HRESULT,
                    [wintypes.UINT, ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
                    i, byref(IID_IApplicationView), byref(p_sub_view),
                )
                if hr_get == 0 and p_sub_view:
                    try:
                        # Check if view itself is pinned
                        is_vp = wintypes.BOOL()
                        call_vtable(p_pinned, 6, HRESULT, [c_void_p, ctypes.POINTER(wintypes.BOOL)], p_sub_view, byref(is_vp))
                        if is_vp.value:
                            continue

                        # Check if base app is pinned
                        aumid_ptr = wintypes.LPWSTR()
                        hr_id = call_vtable(
                            p_sub_view, 17, HRESULT,
                            [ctypes.POINTER(wintypes.LPWSTR)],
                            byref(aumid_ptr),
                        )
                        sub_raw = aumid_ptr.value if hr_id == 0 and aumid_ptr else None
                        if aumid_ptr:
                            ole32.CoTaskMemFree(aumid_ptr)

                        base_id = normalize_base_app_id(sub_raw)
                        if base_id:
                            is_ap = wintypes.BOOL()
                            hr_check = call_vtable(
                                p_pinned, 3, HRESULT,
                                [wintypes.LPCWSTR, ctypes.POINTER(wintypes.BOOL)],
                                base_id, byref(is_ap),
                            )
                            if hr_check == 0 and is_ap.value:
                                call_vtable(p_pinned, 7, HRESULT, [c_void_p], p_sub_view)
                                synced_count += 1
                    finally:
                        safe_release(p_sub_view)
        finally:
            safe_release(p_array)

    return synced_count
