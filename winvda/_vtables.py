"""Curated COM interface identifiers and vtable slot matrices for Windows 10/11."""

from dataclasses import dataclass
import sys
from typing import Optional
import uuid

from winvda._win32 import GUID, py_uuid_to_guid
from winvda.errors import UnsupportedBuildError

# Common Well-Known COM Class & Service GUIDs
CLSID_ImmersiveShell = py_uuid_to_guid(uuid.UUID("{C2F03A33-21F5-47FA-B4BB-156362A2F239}"))
IID_IServiceProvider = py_uuid_to_guid(uuid.UUID("{6D5140C1-7436-11CE-8034-00AA006009FA}"))
IID_IApplicationViewCollection = py_uuid_to_guid(uuid.UUID("{1841C6D7-4F9D-42C0-AF41-8747538F10E5}"))
IID_IApplicationView = py_uuid_to_guid(uuid.UUID("{372E1D3B-38D3-42E4-A15B-8AB2B178F513}"))
IID_IVirtualDesktopPinnedApps = py_uuid_to_guid(uuid.UUID("{4CE81583-1E4C-4632-A621-07A53543148F}"))
CLSID_VirtualDesktopPinnedApps = py_uuid_to_guid(uuid.UUID("{B5A399E7-1C87-46B8-88E9-FC5747B171BD}"))
CLSID_VirtualDesktopManagerInternal = py_uuid_to_guid(uuid.UUID("{C5E0CDCA-7B6E-41B2-9FC4-D93975CC467B}"))

# Notification Service GUIDs
IID_IVirtualDesktopNotification = py_uuid_to_guid(uuid.UUID("{C17949F0-3DE2-4DD0-BE55-520B342BD7AC}"))
IID_IVirtualDesktopNotificationService = py_uuid_to_guid(uuid.UUID("{0CD45E71-5278-4ACD-9686-4973EABF45EA}"))


@dataclass(frozen=True)
class BuildVtableConfig:
    """Vtable slot indices and interface GUIDs for a specific Windows build tier."""

    build_min: int
    build_max: int
    name: str

    manager_iid: GUID
    desktop_iid: GUID

    # Manager slots (IVirtualDesktopManagerInternal)
    slot_get_count: int
    slot_move_view_to_desktop: int
    slot_get_current_desktop: int
    slot_get_desktops: int
    slot_switch_desktop: int
    slot_create_desktop: int
    slot_remove_desktop: int
    slot_find_desktop: int
    slot_set_name: Optional[int]

    # Calling convention flags
    switch_desktop_takes_hwnd: bool
    get_current_takes_hwnd: bool
    get_desktops_takes_hwnd: bool
    create_desktop_takes_hwnd: bool

    # Desktop slots (IVirtualDesktop)
    slot_vd_get_id: int
    slot_vd_get_name: Optional[int]


CONFIG_26100 = BuildVtableConfig(
    build_min=26100,
    build_max=99999,
    name="Windows 11 24H2 / Canary (Build 26100+)",
    manager_iid=py_uuid_to_guid(uuid.UUID("{53F5CA0B-158F-4124-900C-057158060B27}")),
    desktop_iid=py_uuid_to_guid(uuid.UUID("{3F07F4BE-B107-441A-AF0F-39D82529072C}")),
    slot_get_count=3,
    slot_move_view_to_desktop=4,
    slot_get_current_desktop=6,
    slot_get_desktops=7,
    slot_switch_desktop=9,
    slot_create_desktop=11,
    slot_remove_desktop=13,
    slot_find_desktop=14,
    slot_set_name=16,
    switch_desktop_takes_hwnd=False,
    get_current_takes_hwnd=False,
    get_desktops_takes_hwnd=False,
    create_desktop_takes_hwnd=False,
    slot_vd_get_id=4,
    slot_vd_get_name=5,
)

CONFIG_22631 = BuildVtableConfig(
    build_min=22631,
    build_max=26099,
    name="Windows 11 23H2 (Build 22631)",
    manager_iid=py_uuid_to_guid(uuid.UUID("{4970BA3D-FD4E-4647-BEA3-D89076EF4B9C}")),
    desktop_iid=py_uuid_to_guid(uuid.UUID("{3F07F4BE-B107-441A-AF0F-39D82529072C}")),
    slot_get_count=3,
    slot_move_view_to_desktop=4,
    slot_get_current_desktop=6,
    slot_get_desktops=7,
    slot_switch_desktop=9,
    slot_create_desktop=10,
    slot_remove_desktop=12,
    slot_find_desktop=13,
    slot_set_name=15,
    switch_desktop_takes_hwnd=False,
    get_current_takes_hwnd=False,
    get_desktops_takes_hwnd=False,
    create_desktop_takes_hwnd=False,
    slot_vd_get_id=4,
    slot_vd_get_name=5,
)

CONFIG_22621 = BuildVtableConfig(
    build_min=22621,
    build_max=22630,
    name="Windows 11 22H2 (Build 22621)",
    manager_iid=py_uuid_to_guid(uuid.UUID("{A3175F2D-239C-4BD2-8AA0-EEBA8B0B138E}")),
    desktop_iid=py_uuid_to_guid(uuid.UUID("{3F07F4BE-B107-441A-AF0F-39D82529072C}")),
    slot_get_count=3,
    slot_move_view_to_desktop=4,
    slot_get_current_desktop=6,
    slot_get_desktops=7,
    slot_switch_desktop=9,
    slot_create_desktop=10,
    slot_remove_desktop=12,
    slot_find_desktop=13,
    slot_set_name=15,
    switch_desktop_takes_hwnd=False,
    get_current_takes_hwnd=False,
    get_desktops_takes_hwnd=False,
    create_desktop_takes_hwnd=False,
    slot_vd_get_id=4,
    slot_vd_get_name=5,
)

CONFIG_22000 = BuildVtableConfig(
    build_min=22000,
    build_max=22448,
    name="Windows 11 21H2 (Build 22000)",
    manager_iid=py_uuid_to_guid(uuid.UUID("{B2F925B9-5A0F-4D2E-9F4D-2B1507593C10}")),
    desktop_iid=py_uuid_to_guid(uuid.UUID("{536D3495-B208-4CC9-AE26-DE8111275BF8}")),
    slot_get_count=3,
    slot_move_view_to_desktop=4,
    slot_get_current_desktop=6,
    slot_get_desktops=7,
    slot_switch_desktop=9,
    slot_create_desktop=10,
    slot_remove_desktop=12,
    slot_find_desktop=13,
    slot_set_name=15,
    switch_desktop_takes_hwnd=True,
    get_current_takes_hwnd=True,
    get_desktops_takes_hwnd=True,
    create_desktop_takes_hwnd=True,
    slot_vd_get_id=4,
    slot_vd_get_name=6,
)

CONFIG_19041 = BuildVtableConfig(
    build_min=19041,
    build_max=20230,
    name="Windows 10 2004 - 22H2 (Build 19041)",
    manager_iid=py_uuid_to_guid(uuid.UUID("{F31574D6-B682-4CDC-BD56-1827860ABEC6}")),
    desktop_iid=py_uuid_to_guid(uuid.UUID("{FF72FFDD-BE7E-43FC-9C03-AD81681E88E4}")),
    slot_get_count=3,
    slot_move_view_to_desktop=4,
    slot_get_current_desktop=6,
    slot_get_desktops=7,
    slot_switch_desktop=9,
    slot_create_desktop=10,
    slot_remove_desktop=11,
    slot_find_desktop=12,
    slot_set_name=None,
    switch_desktop_takes_hwnd=False,
    get_current_takes_hwnd=False,
    get_desktops_takes_hwnd=False,
    create_desktop_takes_hwnd=False,
    slot_vd_get_id=4,
    slot_vd_get_name=None,
)

ALL_CONFIGS = [CONFIG_26100, CONFIG_22631, CONFIG_22621, CONFIG_22000, CONFIG_19041]


def get_active_build_config() -> BuildVtableConfig:
    """Detect the host Windows build and return the corresponding vtable configuration."""
    if sys.platform != "win32":
        raise UnsupportedBuildError("winvda only runs on Windows (win32)")
    build = sys.getwindowsversion().build
    for cfg in ALL_CONFIGS:
        if cfg.build_min <= build <= cfg.build_max:
            return cfg
    if build >= 26100:
        return CONFIG_26100
    raise UnsupportedBuildError(f"Windows build {build} is not supported by winvda")
