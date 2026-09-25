# winvda

[![PyPI version](https://img.shields.io/pypi/v/winvda.svg)](https://pypi.org/project/winvda/)
[![Python versions](https://img.shields.io/pypi/pyversions/winvda.svg)](https://pypi.org/project/winvda/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE.txt)

> Hardened, zero-cached-state Virtual Desktop engine for Windows 10 and 11.

`winvda` is a lightweight Python library for managing virtual desktops and application pinning on Windows 10 and Windows 11. It is designed specifically for voice control frameworks (Caster, Talon Voice), window managers, and automated desktop environments that require high stability.

---

## Key Improvements Over Legacy `pyvda`

| Dimension | Legacy `pyvda` | `winvda` |
| :--- | :--- | :--- |
| **COM Proxy Lifetime** | Stateful proxies held across arbitrary time. Corrupts on Explorer restart. | **Zero-Cached-State**: Interface pointers acquired and released inside call scope (< 0.02 ms). |
| **Explorer Crash Immunity** | Crashes with `RPC_S_SERVER_UNAVAILABLE`. Requires manual process restart. | **100% Immune**: Automatically binds to newly spawned Explorer instances. |
| **Threading & Apartments** | Thread-local manager leaks COM pointers across threads (`RPC_E_WRONG_THREAD`). | **Stateless Value Objects**: Domain objects are frozen dataclasses with zero COM pointers. |
| **Multi-Window App Pinning** | Fails on secondary Windows Terminal and modern editor windows due to `~Wh~` sub-AUMIDs. | **Task View Parity**: Strips sub-AUMID tokens and pins views individually, matching `twinui.pcshell.dll`. |
| **Runtime Dependencies** | Requires `comtypes`. | **Zero external dependencies**: Pure standard library `ctypes`. |

---

## Installation

Install from PyPI:

```powershell
pip install winvda
```

For local development or running test suites:

```powershell
pip install "winvda[dev]"
```

---

## Quickstart

```python
import winvda

# 1. Enumerate all virtual desktops
desktops = winvda.get_desktops()
for d in desktops:
    print(f"Desktop {d.number}: {d.name} ({d.id})")

# 2. Get current desktop
current = winvda.get_current_desktop()
print(f"Currently on: {current.name}")

# 3. Switch to desktop 2 (by number, UUID, or object)
winvda.switch_desktop(2)

# 4. Pin a window to all desktops
winvda.pin_window(hwnd)

# 5. Pin an entire application (including multi-window / XAML Island instances)
winvda.pin_app(hwnd)
```

---

## Command Line Interface (CLI)

`winvda` includes a diagnostic and automation CLI, callable directly as `winvda` or via `python -m winvda`:

```powershell
# List all desktops and active state
winvda list

# Switch to desktop 3
winvda switch 3

# Pin active foreground window (used by background hotkey daemons / shortcuts)
winvda pin-window

# Pin specific window by HWND (used by scripts / tiling window managers)
winvda pin-window --hwnd 0x1a2b3c

# Wait 2 seconds before capturing foreground window (for interactive terminal use)
winvda pin-window --delay 2

# Pin active application across all desktops
winvda pin-app
```

---

## Threading Model & COM Apartment Architecture

Windows Virtual Desktop management communicates with `explorer.exe` via out-of-process COM RPC. Standard COM wrappers hold long-lived interface pointers and force Single-Threaded Apartment (STA) modes, leading to process instability. `winvda` uses three structural design patterns to guarantee resilience:

### 1. Zero-Cached-State Invocation
`winvda` never persists COM interface pointers in Python instances across calls:
* Every operation executes inside a call-scoped transient session (< 0.02 ms).
* Fresh pointers (`IServiceProvider`, `IVirtualDesktopManagerInternal`) are acquired directly from the active `explorer.exe` instance, invoked atomically, and released immediately.
* When `explorer.exe` terminates, restarts, or crashes, no dead ALPC proxy stubs remain in memory. The subsequent command automatically binds to the newly spawned Explorer process without restart-polling loops or reactive retry decorators.
* If a call occurs during the millisecond window while Explorer is down, `winvda` raises a typed `ShellUnavailableError` instead of crashing.

### 2. Multi-Threaded Apartment (MTA) & Caller Apartment Compatibility
Voice recognition engines (Caster, Talon), async executors, and window managers run on multi-threaded background workers:
* `winvda` joins the Multi-Threaded Apartment (`COINIT_MULTITHREADED`) on invocation, allowing concurrent execution without UI message pumps.
* If the calling thread was already initialized into an STA apartment (by a GUI framework or `pywinauto`), `winvda` detects `RPC_E_CHANGED_MODE` (`0x80010106`), executes safely within the caller's existing apartment, and preserves the caller's threading state upon exit.

### 3. Stateless Value Objects
Domain entities (`VirtualDesktop`, `WindowView`) are immutable frozen dataclasses containing purely primitive data (`UUID`, `int`, `str`, `bool`):
* Value objects store zero COM pointers or RPC proxies.
* They can cross thread boundaries freely, be stored indefinitely, and serialize directly to JSON without triggering `RPC_E_WRONG_THREAD`.

---

## Architecture & Specification

Comprehensive architectural specifications, domain model definitions, error taxonomies, and Windows build matrices are documented in [`docs/SPECIFICATION.md`](docs/SPECIFICATION.md).

---

## Community & Security

* **Contributing**: Development setup, testing workflows, and pull request guidelines are documented in [`CONTRIBUTING.md`](CONTRIBUTING.md).
* **Security Policy**: Vulnerability disclosure instructions and reporting channels are detailed in [`SECURITY.md`](SECURITY.md).

---

## License & Prior Art

Distributed under the **Apache License, Version 2.0**. See [`LICENSE.txt`](LICENSE.txt) for details.

See [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md) for full citations of prior art including Michael Roberts (`pyvda`) and Jari Pennanen (`VirtualDesktopAccessor`).


