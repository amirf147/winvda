"""Immutable domain value objects for winvda.

These models store purely primitive data (UUID, int, str) and hold
zero COM pointers. They are thread-safe and can be passed across
apartments or serialized to JSON without risk of RPC staleness.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass(frozen=True)
class VirtualDesktop:
    """Immutable snapshot of a Windows Virtual Desktop."""

    id: UUID
    number: int
    name: str

    def __str__(self) -> str:
        return f"Desktop {self.number} ('{self.name}', {self.id})"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize desktop state to a plain dictionary."""
        return {
            "id": str(self.id),
            "number": self.number,
            "name": self.name,
        }


@dataclass(frozen=True)
class WindowView:
    """Immutable snapshot of a top-level application window view."""

    hwnd: int
    title: str
    app_id: Optional[str] = None
    base_app_id: Optional[str] = None
    desktop_id: Optional[UUID] = None
    is_pinned: bool = False
    is_app_pinned: bool = False

    @property
    def is_xaml_island(self) -> bool:
        """Indicates whether this window is an isolated secondary frame using a sub-AUMID."""
        return bool(self.app_id and "~Wh~" in self.app_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize window view state to a plain dictionary."""
        return {
            "hwnd": self.hwnd,
            "title": self.title,
            "app_id": self.app_id,
            "base_app_id": self.base_app_id,
            "desktop_id": str(self.desktop_id) if self.desktop_id else None,
            "is_pinned": self.is_pinned,
            "is_app_pinned": self.is_app_pinned,
            "is_xaml_island": self.is_xaml_island,
        }
