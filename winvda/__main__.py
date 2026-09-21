# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""Diagnostic command-line interface for winvda."""

import argparse
import sys
from typing import List

import winvda


def cmd_list(args: argparse.Namespace) -> int:
    current = winvda.get_current_desktop()
    desktops = winvda.get_desktops()

    print("=" * 72)
    print(f"  WinVDA Virtual Desktop Status (Total: {len(desktops)})")
    print("=" * 72)
    for d in desktops:
        marker = "-> [ACTIVE]" if d.id == current.id else "           "
        print(f" {marker} Desktop {d.number}: '{d.name}'")
        print(f"             UUID: {d.id}")
    print("=" * 72)
    return 0


def cmd_current(args: argparse.Namespace) -> int:
    cur = winvda.get_current_desktop()
    print(f"Current Desktop: {cur.number} ('{cur.name}') [{cur.id}]")
    return 0


def cmd_switch(args: argparse.Namespace) -> int:
    target = args.target
    # Try integer index first
    try:
        idx = int(target)
        winvda.switch_desktop(idx)
        print(f"Switched to desktop {idx}.")
        return 0
    except ValueError:
        pass

    winvda.switch_desktop(target)
    print(f"Switched to desktop '{target}'.")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    name = args.name
    new_d = winvda.create_desktop(name=name)
    print(f"Created new virtual desktop: {new_d.number} ('{new_d.name}') [{new_d.id}]")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    target = args.target
    try:
        target = int(target)
    except ValueError:
        pass
    winvda.remove_desktop(target)
    print(f"Removed virtual desktop: {target}.")
    return 0


def cmd_rename(args: argparse.Namespace) -> int:
    target = args.target
    name = args.name
    try:
        target = int(target)
    except ValueError:
        pass
    winvda.set_desktop_name(target, name)
    print(f"Renamed desktop {target} to '{name}'.")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    count = winvda.sync_pinned_apps()
    print(f"Synchronized pinned multi-window applications. Views updated: {count}.")
    return 0


def _resolve_hwnd(args: argparse.Namespace) -> int:
    import time

    if getattr(args, "delay", 0) and args.delay > 0:
        print(f"Waiting {args.delay:.1f}s before capturing foreground window...")
        time.sleep(args.delay)

    if getattr(args, "hwnd", None) is not None:
        val = str(args.hwnd).strip()
        try:
            if val.lower().startswith("0x"):
                hwnd = int(val, 16)
            else:
                hwnd = int(val)
        except ValueError:
            raise winvda.VdaError(f"Invalid HWND format: '{args.hwnd}'")
    else:
        hwnd = winvda.get_foreground_window()
        if not hwnd:
            raise winvda.WindowNotFoundError("No active foreground window found.")

    return hwnd


def cmd_pin_window(args: argparse.Namespace) -> int:
    from winvda._win32 import get_window_title

    hwnd = _resolve_hwnd(args)
    title = get_window_title(hwnd)
    winvda.pin_window(hwnd)
    label = f"'{title}' ({hwnd:#x})" if title else f"HWND {hwnd:#x}"
    print(f"Pinned window {label} to all virtual desktops.")
    return 0


def cmd_unpin_window(args: argparse.Namespace) -> int:
    from winvda._win32 import get_window_title

    hwnd = _resolve_hwnd(args)
    title = get_window_title(hwnd)
    winvda.unpin_window(hwnd)
    label = f"'{title}' ({hwnd:#x})" if title else f"HWND {hwnd:#x}"
    print(f"Unpinned window {label} from all virtual desktops.")
    return 0


def cmd_pin_app(args: argparse.Namespace) -> int:
    from winvda._win32 import get_window_title

    hwnd = _resolve_hwnd(args)
    title = get_window_title(hwnd)
    winvda.pin_app(hwnd)
    label = f"'{title}' ({hwnd:#x})" if title else f"HWND {hwnd:#x}"
    print(f"Pinned application {label} across all virtual desktops.")
    return 0


def cmd_unpin_app(args: argparse.Namespace) -> int:
    from winvda._win32 import get_window_title

    hwnd = _resolve_hwnd(args)
    title = get_window_title(hwnd)
    winvda.unpin_app(hwnd)
    label = f"'{title}' ({hwnd:#x})" if title else f"HWND {hwnd:#x}"
    print(f"Unpinned application {label} from all virtual desktops.")
    return 0


def main(argv: List[str] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="winvda", description="WinVDA CLI management tool")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    sub_list = subparsers.add_parser("list", help="List all virtual desktops")
    sub_list.set_defaults(func=cmd_list)

    sub_cur = subparsers.add_parser("current", help="Show the currently active virtual desktop")
    sub_cur.set_defaults(func=cmd_current)

    sub_switch = subparsers.add_parser("switch", help="Switch to a virtual desktop (by index, name, or UUID)")
    sub_switch.add_argument("target", help="Desktop number, name, or UUID")
    sub_switch.set_defaults(func=cmd_switch)

    sub_create = subparsers.add_parser("create", help="Create a new virtual desktop")
    sub_create.add_argument("--name", "-n", default=None, help="Optional name for the new desktop")
    sub_create.set_defaults(func=cmd_create)

    sub_remove = subparsers.add_parser("remove", help="Remove a virtual desktop")
    sub_remove.add_argument("target", help="Desktop number, name, or UUID to remove")
    sub_remove.set_defaults(func=cmd_remove)

    sub_rename = subparsers.add_parser("rename", help="Rename a virtual desktop")
    sub_rename.add_argument("target", help="Desktop number, name, or UUID")
    sub_rename.add_argument("name", help="New name for the desktop")
    sub_rename.set_defaults(func=cmd_rename)

    sub_sync = subparsers.add_parser("sync", help="Synchronize multi-window application pinning")
    sub_sync.set_defaults(func=cmd_sync)

    # pin-window
    sub_pin_w = subparsers.add_parser(
        "pin-window",
        help="Pin a window across all virtual desktops (defaults to foreground window)",
    )
    sub_pin_w.add_argument(
        "--hwnd",
        "-w",
        help="Window handle in hex or decimal (defaults to active foreground window)",
    )
    sub_pin_w.add_argument(
        "--delay",
        "-d",
        type=float,
        default=0.0,
        help="Seconds to wait before capturing active foreground window",
    )
    sub_pin_w.set_defaults(func=cmd_pin_window)

    # unpin-window
    sub_unpin_w = subparsers.add_parser(
        "unpin-window",
        help="Unpin a window from all virtual desktops (defaults to foreground window)",
    )
    sub_unpin_w.add_argument(
        "--hwnd",
        "-w",
        help="Window handle in hex or decimal (defaults to active foreground window)",
    )
    sub_unpin_w.add_argument(
        "--delay",
        "-d",
        type=float,
        default=0.0,
        help="Seconds to wait before capturing active foreground window",
    )
    sub_unpin_w.set_defaults(func=cmd_unpin_window)

    # pin-app
    sub_pin_a = subparsers.add_parser(
        "pin-app",
        help="Pin an application across all virtual desktops (defaults to foreground window)",
    )
    sub_pin_a.add_argument(
        "--hwnd",
        "-w",
        help="Window handle in hex or decimal (defaults to active foreground window)",
    )
    sub_pin_a.add_argument(
        "--delay",
        "-d",
        type=float,
        default=0.0,
        help="Seconds to wait before capturing active foreground window",
    )
    sub_pin_a.set_defaults(func=cmd_pin_app)

    # unpin-app
    sub_unpin_a = subparsers.add_parser(
        "unpin-app",
        help="Unpin an application from all virtual desktops (defaults to foreground window)",
    )
    sub_unpin_a.add_argument(
        "--hwnd",
        "-w",
        help="Window handle in hex or decimal (defaults to active foreground window)",
    )
    sub_unpin_a.add_argument(
        "--delay",
        "-d",
        type=float,
        default=0.0,
        help="Seconds to wait before capturing active foreground window",
    )
    sub_unpin_a.set_defaults(func=cmd_unpin_app)

    if not argv:
        parser.print_help()
        return 0

    parsed = parser.parse_args(argv)
    if hasattr(parsed, "func"):
        try:
            return parsed.func(parsed)
        except winvda.VdaError as e:
            print(f"WinVDA Error: {e}", file=sys.stderr)
            return 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
