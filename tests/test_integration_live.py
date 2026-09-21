# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""Live integration tests executed against running Windows Shell."""

import winvda


def test_live_get_desktops():
    desktops = winvda.get_desktops()
    assert len(desktops) >= 1
    for idx, d in enumerate(desktops):
        assert d.number == idx + 1
        assert d.id is not None
        assert isinstance(d.name, str)


def test_live_get_current_desktop():
    cur = winvda.get_current_desktop()
    assert cur is not None
    assert cur.number >= 1
    assert cur.id is not None


def test_live_sync_pinned_apps():
    synced = winvda.sync_pinned_apps()
    assert isinstance(synced, int)
    assert synced >= 0


def test_live_desktop_create_rename_remove():
    initial_count = len(winvda.get_desktops())

    # Create
    new_d = winvda.create_desktop(name="Pytest Temporary Desktop")
    assert new_d is not None
    assert new_d.name == "Pytest Temporary Desktop"
    assert len(winvda.get_desktops()) == initial_count + 1

    # Rename
    winvda.set_desktop_name(new_d.id, "Pytest Renamed Desktop")
    renamed_d = [d for d in winvda.get_desktops() if d.id == new_d.id][0]
    assert renamed_d.name == "Pytest Renamed Desktop"

    # Remove
    winvda.remove_desktop(new_d.id)
    assert len(winvda.get_desktops()) == initial_count
