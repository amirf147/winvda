# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""Unit tests for Task View parity sub-AUMID normalization."""

from winvda.pinning import normalize_base_app_id


def test_normalize_base_app_id_standard():
    assert normalize_base_app_id(None) is None
    assert normalize_base_app_id("") is None
    assert normalize_base_app_id("Microsoft.Windows.Explorer") == "Microsoft.Windows.Explorer"
    assert normalize_base_app_id("Waterfox.6F940AC27A98DD61") == "Waterfox.6F940AC27A98DD61"


def test_normalize_base_app_id_xaml_island():
    # Windows Terminal secondary window
    raw_terminal = "Microsoft.WindowsTerminal_8wekyb3d8bbwe!App~Wh~w00620A28"
    assert normalize_base_app_id(raw_terminal) == "Microsoft.WindowsTerminal_8wekyb3d8bbwe!App"

    # Antigravity / Electron detached frame
    raw_ide = "Google.AntigravityIDE~Wh~w00030C42"
    assert normalize_base_app_id(raw_ide) == "Google.AntigravityIDE"
