"""Exception taxonomy for winvda."""

from typing import Optional


class VdaError(Exception):
    """Base exception for all winvda operations."""
    pass


class VdaComError(VdaError):
    """Raised when an underlying Windows COM call fails."""

    def __init__(self, hresult: int, message: str, context: Optional[str] = None) -> None:
        self.hresult = hresult
        self.message = message
        self.context = context
        hex_code = f"0x{hresult & 0xFFFFFFFF:08X}"
        detail = f"{message} (HRESULT {hex_code})"
        if context:
            detail = f"[{context}] {detail}"
        super().__init__(detail)


class ShellUnavailableError(VdaComError):
    """Raised when explorer.exe is unavailable, restarting, or the ALPC endpoint closed."""
    pass


class DesktopNotFoundError(VdaError):
    """Raised when a requested virtual desktop cannot be located by ID or index."""
    pass


class WindowNotFoundError(VdaError):
    """Raised when an HWND is invalid, destroyed, or inaccessible."""
    pass


class UnsupportedBuildError(VdaError):
    """Raised when the active Windows build has no mapped COM vtable interface."""
    pass
