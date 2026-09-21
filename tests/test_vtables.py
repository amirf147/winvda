# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""Unit tests for Windows build vtable mapping."""

from winvda._vtables import (
    ALL_CONFIGS,
    CONFIG_19041,
    CONFIG_22000,
    CONFIG_22621,
    CONFIG_22631,
    CONFIG_26100,
    get_active_build_config,
)


def test_active_build_config_detection():
    config = get_active_build_config()
    assert config is not None
    assert config.slot_get_count == 3
    assert config.slot_get_desktops == 7
    assert config.slot_vd_get_id == 4


def test_all_configs_integrity():
    for cfg in ALL_CONFIGS:
        assert cfg.build_min > 0
        assert cfg.build_max >= cfg.build_min
        assert cfg.slot_get_count == 3
        assert cfg.slot_get_desktops == 7
        assert cfg.slot_vd_get_id == 4
        assert cfg.name

    assert CONFIG_19041.build_min == 19041
    assert CONFIG_22000.build_min == 22000
    assert CONFIG_22621.build_min == 22621
    assert CONFIG_22631.build_min == 22631
    assert CONFIG_26100.build_min == 26100
