"""Unit tests for Windows build vtable mapping."""

from winvda._vtables import get_active_build_config, CONFIG_26100, CONFIG_22631, CONFIG_22621, CONFIG_22000, CONFIG_19041


def test_active_build_config_detection():
    config = get_active_build_config()
    assert config is not None
    assert config.slot_get_count == 3
    assert config.slot_get_desktops == 7
    assert config.slot_vd_get_id == 4
