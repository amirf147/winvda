# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""winvda - Hardened, zero-cached-state Virtual Desktop engine for Windows 10 and 11."""

__version__ = "0.1.0"
__author__ = "Amir Farhadi"
__license__ = "Apache-2.0"

from winvda._win32 import get_foreground_window
from winvda.engine import (
    create_desktop,
    get_current_desktop,
    get_desktops,
    move_window_to_desktop,
    remove_desktop,
    set_desktop_name,
    switch_desktop,
)
from winvda.errors import (
    DesktopNotFoundError,
    ShellUnavailableError,
    UnsupportedBuildError,
    VdaComError,
    VdaError,
    WindowNotFoundError,
)
from winvda.pinning import (
    get_window_view,
    is_app_pinned,
    is_window_pinned,
    normalize_base_app_id,
    pin_app,
    pin_window,
    sync_pinned_apps,
    toggle_pin_app,
    toggle_pin_window,
    unpin_app,
    unpin_window,
)
from winvda.types import (
    VirtualDesktop,
    WindowView,
)

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__license__",
    # Models
    "VirtualDesktop",
    "WindowView",
    # Exceptions
    "VdaError",
    "VdaComError",
    "ShellUnavailableError",
    "DesktopNotFoundError",
    "WindowNotFoundError",
    "UnsupportedBuildError",
    # Engine Operations
    "get_desktops",
    "get_current_desktop",
    "switch_desktop",
    "create_desktop",
    "remove_desktop",
    "set_desktop_name",
    "move_window_to_desktop",
    # Pinning Operations
    "get_window_view",
    "is_window_pinned",
    "pin_window",
    "unpin_window",
    "toggle_pin_window",
    "is_app_pinned",
    "pin_app",
    "unpin_app",
    "toggle_pin_app",
    "sync_pinned_apps",
    "normalize_base_app_id",
    # Utilities
    "get_foreground_window",
]
