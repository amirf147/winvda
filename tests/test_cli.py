"""Unit tests for winvda command-line interface parsing."""

import argparse
import pytest
from winvda.__main__ import _resolve_hwnd, main
from winvda.errors import VdaError


def test_cli_help(capsys):
    ret = main([])
    assert ret == 0
    captured = capsys.readouterr()
    assert "pin-window" in captured.out
    assert "pin-app" in captured.out


def test_cli_invalid_hwnd():
    args = argparse.Namespace(hwnd="not_a_number", delay=0.0)
    with pytest.raises(VdaError, match="Invalid HWND format"):
        _resolve_hwnd(args)


def test_cli_hex_hwnd():
    args = argparse.Namespace(hwnd="0x1234", delay=0.0)
    assert _resolve_hwnd(args) == 0x1234


def test_cli_decimal_hwnd():
    args = argparse.Namespace(hwnd="4660", delay=0.0)
    assert _resolve_hwnd(args) == 4660
