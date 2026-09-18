# WinVDA Technical Specification

## 1. Executive Summary

`winvda` is a lightweight, zero-dependency Python library for querying, switching, and manipulating Windows 10 and 11 Virtual Desktops.

It replaces the legacy `pyvda` library by eliminating stateful COM proxy caching, cross-apartment thread violations, and unhandled `~Wh~` sub-AUMID application pinning failures.

---

## 2. Core Architectural Principles

### 2.1 Zero-Cached-State (Call-Scoped Transient Invocation)
Long-running out-of-process COM interface pointers to `explorer.exe` (`IVirtualDesktopManagerInternal`, `IApplicationView`, `IVirtualDesktopPinnedApps`) are never cached in persistent Python instances.
* Every operation executes inside a call-scoped worker on a dedicated Multithreaded Apartment (MTA) thread.
* The worker acquires fresh interface pointers via `IServiceProvider::QueryService`, invokes the requested atomic method, and releases pointers immediately.
* When `explorer.exe` restarts, the next call automatically binds to the new process instance without dead proxy stubs (`RPC_S_SERVER_UNAVAILABLE`).

### 2.2 Stateless Immutable Value Objects
Domain entities are modeled as frozen dataclasses:
```python
@dataclass(frozen=True)
class VirtualDesktop:
    id: UUID
    number: int
    name: str

@dataclass(frozen=True)
class WindowView:
    hwnd: int
    title: str
    app_id: Optional[str]
    base_app_id: Optional[str]
    desktop_id: Optional[UUID]
    is_pinned: bool
    is_app_pinned: bool
```
Value objects contain zero COM pointers. They can cross thread boundaries safely and serialize directly to JSON.

### 2.3 Task View Parity Pinning
Modern hosted applications (Windows Terminal, VS Code, Slack) assign dynamic sub-AUMIDs (`<Package>!App~Wh~w<HEX_HWND>`) to secondary windows.
* `winvda` parses and normalizes the canonical package identity (`base_app_id`).
* Pinning an application registers the base identity in the Windows Shell pinned database while calling `PinView` individually on active sub-windows, matching the native Task View execution path in `twinui.pcshell.dll`.

---

## 3. Windows OS Build Support Matrix

| Build Range | Windows Release | Manager Service GUID | Key Vtable Changes |
| :--- | :--- | :--- | :--- |
| **10240 - 14392** | Windows 10 1507 | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | Initial 10-method layout. |
| **14393 - 17762** | Windows 10 1607 - 1809 | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | Added `GetAdjacentDesktop`. |
| **19041 - 20230** | Windows 10 2004 - 21H2 | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | Slot 9 `SwitchDesktop`. |
| **20231 - 21312** | Windows 10 Preview | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | Added HWND parameters to `GetCurrentDesktop`. |
| **21313 - 22448** | Windows 10/11 Preview | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | Added wallpaper and desktop name APIs. |
| **22000** | Windows 11 21H2 | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | Desktop naming, custom wallpapers. |
| **22621 - 22630** | Windows 11 22H2 | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | `SwitchDesktop(IVirtualDesktop*)` without HWND. |
| **22631 - 26099** | Windows 11 23H2 | `{C5E0CDCA-22AC-4E2F-A0AD-4D12E9A7F275}` | Added remote desktop support. |
| **26100+** | Windows 11 24H2 | `{0F3A72B0-4566-487E-9A33-4ED302F6D6CE}` | Updated manager GUID and method slots. |

---

## 4. Error Taxonomy

* `VdaError`: Base exception for all library errors.
* `ShellUnavailableError`: Raised when `explorer.exe` is restarting or its COM ALPC port is unavailable.
* `DesktopNotFoundError`: Raised when an index or UUID does not map to an existing desktop.
* `WindowNotFoundError`: Raised when an HWND is invalid or cannot be inspected.
* `UnsupportedBuildError`: Raised on non-Windows platforms or unmapped build tiers.
