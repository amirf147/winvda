# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""Decoupled asynchronous event sink for Windows Virtual Desktop notifications."""

import queue
import threading
from typing import Callable, Optional
from uuid import UUID

from winvda._win32 import COINIT_MULTITHREADED, ole32


class VirtualDesktopEvent:
    """Base event payload emitted by the notification sink."""

    def __init__(
        self,
        event_type: str,
        old_desktop_id: Optional[UUID] = None,
        new_desktop_id: Optional[UUID] = None,
    ) -> None:
        self.event_type = event_type
        self.old_desktop_id = old_desktop_id
        self.new_desktop_id = new_desktop_id

    def __repr__(self) -> str:
        return f"VirtualDesktopEvent(type='{self.event_type}', old={self.old_desktop_id}, new={self.new_desktop_id})"


class DesktopEventListener:
    """Background listener hosting an in-memory IVirtualDesktopNotification sink.

    Dispatches external desktop switches (touchpad swipes, native shortcuts) into
    a thread-safe queue without blocking caller or speech recognition loops.
    """

    def __init__(self, on_event: Optional[Callable[[VirtualDesktopEvent], None]] = None) -> None:
        self.events: "queue.Queue[VirtualDesktopEvent]" = queue.Queue()
        self._callback = on_event
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the background event listener thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="WinVDA-EventListener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the background listener to terminate."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        """Background thread message pump and notification sink loop."""
        ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.25)
        finally:
            ole32.CoUninitialize()
