"""Unit tests for winvda immutable value objects."""

from uuid import UUID
import pytest
from winvda.types import VirtualDesktop, WindowView


def test_virtual_desktop_immutability():
    uid = UUID("b81e302b-192e-47ef-ba32-501d5dd59192")
    vd = VirtualDesktop(id=uid, number=1, name="Primary")

    assert vd.id == uid
    assert vd.number == 1
    assert vd.name == "Primary"

    with pytest.raises(AttributeError):
        vd.number = 2  # Frozen dataclass must reject mutation


def test_virtual_desktop_to_dict():
    uid = UUID("8cfc4b50-e3ca-4399-b698-f0fa92819735")
    vd = VirtualDesktop(id=uid, number=2, name="Secondary")
    data = vd.to_dict()

    assert data["id"] == str(uid)
    assert data["number"] == 2
    assert data["name"] == "Secondary"


def test_window_view_xaml_island_detection():
    # Regular classic window
    classic = WindowView(hwnd=0x1234, title="Notepad", app_id="Microsoft.Windows.Notepad")
    assert not classic.is_xaml_island
    assert classic.base_app_id is None

    # XAML Island hosted window
    sub_aumid = "Microsoft.WindowsTerminal_8wekyb3d8bbwe!App~Wh~w00620A28"
    xaml_win = WindowView(hwnd=0x5678, title="Terminal", app_id=sub_aumid, base_app_id="Microsoft.WindowsTerminal_8wekyb3d8bbwe!App")
    assert xaml_win.is_xaml_island
    assert xaml_win.base_app_id == "Microsoft.WindowsTerminal_8wekyb3d8bbwe!App"
