# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""Call-scoped transient MTA execution engine for Windows Virtual Desktops.

This module provides the core desktop management functions. Every function
acquires fresh COM pointers inside its call scope, performs the requested
operation, and immediately releases all pointers. No COM interface pointers
are ever persisted across function calls.
"""

import ctypes
from contextlib import contextmanager
from ctypes import byref, c_void_p, wintypes
from typing import Generator, List, Optional, Tuple, Union
from uuid import UUID

from winvda._vtables import (
    CLSID_ImmersiveShell,
    CLSID_VirtualDesktopManagerInternal,
    IID_IApplicationViewCollection,
    IID_IServiceProvider,
    get_active_build_config,
)
from winvda._win32 import (
    CLSCTX_LOCAL_SERVER,
    COINIT_MULTITHREADED,
    GUID,
    HRESULT,
    call_vtable,
    check_hresult,
    create_hstring,
    guid_to_py_uuid,
    ole32,
    py_uuid_to_guid,
    read_hstring,
    safe_release,
)
from winvda.errors import DesktopNotFoundError, UnsupportedBuildError, VdaComError
from winvda.types import VirtualDesktop


@contextmanager
def transient_mta_session() -> Generator[Tuple[c_void_p, c_void_p], None, None]:
    """Context manager for a call-scoped transient MTA COM invocation session.

    Acquires IServiceProvider and IVirtualDesktopManagerInternal from explorer.exe,
    yields them for atomic execution, and guarantees safe release of all interface
    pointers and COM uninitialization upon exit.
    """
    config = get_active_build_config()
    hr_init = ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
    # S_FALSE (0x1) means already initialized on this thread, which is fine
    co_initialized = hr_init >= 0

    p_sp = c_void_p()
    p_vdm = c_void_p()
    try:
        hr_sp = ole32.CoCreateInstance(
            byref(CLSID_ImmersiveShell),
            None,
            CLSCTX_LOCAL_SERVER,
            byref(IID_IServiceProvider),
            byref(p_sp),
        )
        check_hresult(hr_sp, "CoCreateInstance(CLSID_ImmersiveShell)")

        hr_vdm = call_vtable(
            p_sp,
            3,  # IServiceProvider::QueryService
            HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(CLSID_VirtualDesktopManagerInternal),
            byref(config.manager_iid),
            byref(p_vdm),
        )
        check_hresult(hr_vdm, "QueryService(IVirtualDesktopManagerInternal)")

        yield (p_sp, p_vdm)
    finally:
        safe_release(p_vdm)
        safe_release(p_sp)
        if co_initialized:
            ole32.CoUninitialize()


def get_desktops() -> List[VirtualDesktop]:
    """Enumerate all existing virtual desktops as immutable value objects."""
    config = get_active_build_config()
    desktops: List[VirtualDesktop] = []

    with transient_mta_session() as (p_sp, p_vdm):
        p_array = c_void_p()
        if config.get_desktops_takes_hwnd:
            hr_gd = call_vtable(
                p_vdm,
                config.slot_get_desktops,
                HRESULT,
                [wintypes.HWND, ctypes.POINTER(c_void_p)],
                0,
                byref(p_array),
            )
        else:
            hr_gd = call_vtable(
                p_vdm,
                config.slot_get_desktops,
                HRESULT,
                [ctypes.POINTER(c_void_p)],
                byref(p_array),
            )
        check_hresult(hr_gd, "IVirtualDesktopManagerInternal::GetDesktops")

        try:
            arr_len = wintypes.UINT()
            hr_len = call_vtable(
                p_array,
                3,
                HRESULT,  # IObjectArray::GetCount
                [ctypes.POINTER(wintypes.UINT)],
                byref(arr_len),
            )
            check_hresult(hr_len, "IObjectArray::GetCount")

            for i in range(arr_len.value):
                p_vd = c_void_p()
                hr_get = call_vtable(
                    p_array,
                    4,
                    HRESULT,  # IObjectArray::GetAt
                    [wintypes.UINT, ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
                    i,
                    byref(config.desktop_iid),
                    byref(p_vd),
                )
                if hr_get != 0 or not p_vd:
                    continue

                try:
                    # GetId
                    c_guid = GUID()
                    hr_id = call_vtable(
                        p_vd,
                        config.slot_vd_get_id,
                        HRESULT,
                        [ctypes.POINTER(GUID)],
                        byref(c_guid),
                    )
                    check_hresult(hr_id, "IVirtualDesktop::GetId")
                    d_id = guid_to_py_uuid(c_guid)

                    # GetName
                    d_name = ""
                    if config.slot_vd_get_name is not None:
                        hstr = c_void_p()
                        hr_name = call_vtable(
                            p_vd,
                            config.slot_vd_get_name,
                            HRESULT,
                            [ctypes.POINTER(c_void_p)],
                            byref(hstr),
                        )
                        if hr_name == 0 and hstr:
                            d_name = read_hstring(hstr)

                    if not d_name:
                        d_name = f"Desktop {i + 1}"

                    desktops.append(VirtualDesktop(id=d_id, number=i + 1, name=d_name))
                finally:
                    safe_release(p_vd)
        finally:
            safe_release(p_array)

    return desktops


def get_current_desktop() -> VirtualDesktop:
    """Retrieve the currently active virtual desktop as an immutable value object."""
    config = get_active_build_config()
    with transient_mta_session() as (p_sp, p_vdm):
        p_cur = c_void_p()
        if config.get_current_takes_hwnd:
            hr_cur = call_vtable(
                p_vdm,
                config.slot_get_current_desktop,
                HRESULT,
                [wintypes.HWND, ctypes.POINTER(c_void_p)],
                0,
                byref(p_cur),
            )
        else:
            hr_cur = call_vtable(
                p_vdm,
                config.slot_get_current_desktop,
                HRESULT,
                [ctypes.POINTER(c_void_p)],
                byref(p_cur),
            )
        check_hresult(hr_cur, "IVirtualDesktopManagerInternal::GetCurrentDesktop")

        try:
            c_guid = GUID()
            hr_id = call_vtable(
                p_cur,
                config.slot_vd_get_id,
                HRESULT,
                [ctypes.POINTER(GUID)],
                byref(c_guid),
            )
            check_hresult(hr_id, "IVirtualDesktop::GetId")
            cur_id = guid_to_py_uuid(c_guid)
        finally:
            safe_release(p_cur)

    # Match against full enumeration to determine index and name accurately
    all_desktops = get_desktops()
    for d in all_desktops:
        if d.id == cur_id:
            return d

    return VirtualDesktop(id=cur_id, number=1, name="Desktop 1")


def _resolve_target_uuid(target: Union[VirtualDesktop, UUID, int, str]) -> UUID:
    """Normalize a target desktop parameter (object, UUID, number, or string) to a UUID."""
    if isinstance(target, VirtualDesktop):
        return target.id
    if isinstance(target, UUID):
        return target
    if isinstance(target, int):
        desktops = get_desktops()
        if 1 <= target <= len(desktops):
            return desktops[target - 1].id
        raise DesktopNotFoundError(f"Desktop index {target} out of range (1 to {len(desktops)})")
    if isinstance(target, str):
        try:
            return UUID(target)
        except ValueError:
            # Check by name
            desktops = get_desktops()
            for d in desktops:
                if d.name.lower() == target.lower():
                    return d.id
            raise DesktopNotFoundError(f"No virtual desktop found matching name '{target}'")
    raise TypeError(f"Invalid target desktop specification: {type(target)}")


def switch_desktop(target: Union[VirtualDesktop, UUID, int, str]) -> None:
    """Switch the active view to the specified virtual desktop."""
    target_id = _resolve_target_uuid(target)
    config = get_active_build_config()

    with transient_mta_session() as (p_sp, p_vdm):
        # Locate target IVirtualDesktop pointer via FindDesktop
        p_target_vd = c_void_p()
        target_guid = py_uuid_to_guid(target_id)
        hr_find = call_vtable(
            p_vdm,
            config.slot_find_desktop,
            HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(target_guid),
            byref(p_target_vd),
        )
        check_hresult(hr_find, "IVirtualDesktopManagerInternal::FindDesktop")
        if not p_target_vd:
            raise DesktopNotFoundError(f"Virtual desktop {target_id} not found by shell")

        try:
            if config.switch_desktop_takes_hwnd:
                hr_switch = call_vtable(
                    p_vdm,
                    config.slot_switch_desktop,
                    HRESULT,
                    [wintypes.HWND, c_void_p],
                    0,
                    p_target_vd,
                )
            else:
                hr_switch = call_vtable(p_vdm, config.slot_switch_desktop, HRESULT, [c_void_p], p_target_vd)
            check_hresult(hr_switch, "IVirtualDesktopManagerInternal::SwitchDesktop")
        finally:
            safe_release(p_target_vd)


def create_desktop(name: Optional[str] = None) -> VirtualDesktop:
    """Create a new virtual desktop, optionally assigning a custom name."""
    config = get_active_build_config()

    with transient_mta_session() as (p_sp, p_vdm):
        p_new_vd = c_void_p()
        if config.create_desktop_takes_hwnd:
            hr_create = call_vtable(
                p_vdm,
                config.slot_create_desktop,
                HRESULT,
                [wintypes.HWND, ctypes.POINTER(c_void_p)],
                0,
                byref(p_new_vd),
            )
        else:
            hr_create = call_vtable(
                p_vdm,
                config.slot_create_desktop,
                HRESULT,
                [ctypes.POINTER(c_void_p)],
                byref(p_new_vd),
            )
        check_hresult(hr_create, "IVirtualDesktopManagerInternal::CreateDesktopW")

        try:
            c_guid = GUID()
            hr_id = call_vtable(
                p_new_vd,
                config.slot_vd_get_id,
                HRESULT,
                [ctypes.POINTER(GUID)],
                byref(c_guid),
            )
            check_hresult(hr_id, "IVirtualDesktop::GetId")
            new_id = guid_to_py_uuid(c_guid)

            if name and config.slot_set_name is not None:
                hstr = create_hstring(name)
                try:
                    hr_name = call_vtable(
                        p_vdm,
                        config.slot_set_name,
                        HRESULT,
                        [c_void_p, c_void_p],
                        p_new_vd,
                        hstr,
                    )
                    check_hresult(hr_name, "IVirtualDesktopManagerInternal::SetName")
                finally:
                    pass
        finally:
            safe_release(p_new_vd)

    # Return refreshed desktop value object
    desktops = get_desktops()
    for d in desktops:
        if d.id == new_id:
            return d

    return VirtualDesktop(id=new_id, number=len(desktops), name=name or f"Desktop {len(desktops)}")


def remove_desktop(
    target: Union[VirtualDesktop, UUID, int, str],
    fallback: Optional[Union[VirtualDesktop, UUID, int, str]] = None,
) -> None:
    """Remove a virtual desktop, moving its windows to a fallback desktop."""
    target_id = _resolve_target_uuid(target)
    fallback_id = _resolve_target_uuid(fallback) if fallback else None

    # Default fallback: first available desktop not equal to target
    if not fallback_id:
        desktops = get_desktops()
        if len(desktops) <= 1:
            raise VdaComError(0x80004005, "Cannot remove the sole remaining virtual desktop")
        for d in desktops:
            if d.id != target_id:
                fallback_id = d.id
                break

    if fallback_id == target_id:
        raise ValueError("Fallback desktop cannot be the desktop being destroyed")

    config = get_active_build_config()
    with transient_mta_session() as (p_sp, p_vdm):
        p_destroy = c_void_p()
        p_fallback = c_void_p()

        g_destroy = py_uuid_to_guid(target_id)
        hr_f1 = call_vtable(
            p_vdm,
            config.slot_find_desktop,
            HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(g_destroy),
            byref(p_destroy),
        )
        check_hresult(hr_f1, "FindDesktop(destroy)")

        g_fallback = py_uuid_to_guid(fallback_id)
        hr_f2 = call_vtable(
            p_vdm,
            config.slot_find_desktop,
            HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(g_fallback),
            byref(p_fallback),
        )
        check_hresult(hr_f2, "FindDesktop(fallback)")

        try:
            hr_rem = call_vtable(
                p_vdm,
                config.slot_remove_desktop,
                HRESULT,
                [c_void_p, c_void_p],
                p_destroy,
                p_fallback,
            )
            check_hresult(hr_rem, "IVirtualDesktopManagerInternal::RemoveDesktop")
        finally:
            safe_release(p_destroy)
            safe_release(p_fallback)


def set_desktop_name(target: Union[VirtualDesktop, UUID, int, str], name: str) -> None:
    """Rename an existing virtual desktop."""
    target_id = _resolve_target_uuid(target)
    config = get_active_build_config()
    if config.slot_set_name is None:
        raise UnsupportedBuildError("Desktop renaming is not supported on this Windows build")

    with transient_mta_session() as (p_sp, p_vdm):
        p_vd = c_void_p()
        g_target = py_uuid_to_guid(target_id)
        hr_find = call_vtable(
            p_vdm,
            config.slot_find_desktop,
            HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(g_target),
            byref(p_vd),
        )
        check_hresult(hr_find, "FindDesktop")

        try:
            hstr = create_hstring(name)
            hr_set = call_vtable(p_vdm, config.slot_set_name, HRESULT, [c_void_p, c_void_p], p_vd, hstr)
            check_hresult(hr_set, "IVirtualDesktopManagerInternal::SetName")
        finally:
            safe_release(p_vd)


def move_window_to_desktop(hwnd: int, target: Union[VirtualDesktop, UUID, int, str]) -> None:
    """Move a specific top-level window to a target virtual desktop."""
    target_id = _resolve_target_uuid(target)
    config = get_active_build_config()

    with transient_mta_session() as (p_sp, p_vdm):
        # Query IApplicationViewCollection
        p_avc = c_void_p()
        hr_avc = call_vtable(
            p_sp,
            3,
            HRESULT,
            [ctypes.POINTER(GUID), ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
            byref(IID_IApplicationViewCollection),
            byref(IID_IApplicationViewCollection),
            byref(p_avc),
        )
        check_hresult(hr_avc, "QueryService(IApplicationViewCollection)")

        p_view = c_void_p()
        p_vd = c_void_p()
        try:
            # Slot 6: GetViewForHwnd
            hr_gv = call_vtable(
                p_avc,
                6,
                HRESULT,
                [wintypes.HWND, ctypes.POINTER(c_void_p)],
                hwnd,
                byref(p_view),
            )
            check_hresult(hr_gv, "IApplicationViewCollection::GetViewForHwnd")

            g_target = py_uuid_to_guid(target_id)
            hr_find = call_vtable(
                p_vdm,
                config.slot_find_desktop,
                HRESULT,
                [ctypes.POINTER(GUID), ctypes.POINTER(c_void_p)],
                byref(g_target),
                byref(p_vd),
            )
            check_hresult(hr_find, "FindDesktop")

            hr_move = call_vtable(
                p_vdm,
                config.slot_move_view_to_desktop,
                HRESULT,
                [c_void_p, c_void_p],
                p_view,
                p_vd,
            )
            check_hresult(hr_move, "IVirtualDesktopManagerInternal::MoveViewToDesktop")
        finally:
            safe_release(p_view)
            safe_release(p_vd)
            safe_release(p_avc)
