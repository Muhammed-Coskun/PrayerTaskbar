"""
Win32 API helpers for Windows taskbar integration.

Provides low-level Win32 functions for:
- Finding all taskbars (primary + secondary monitors)
- Injecting a widget into the taskbar as a child window
- Querying window and client rectangles
- Validating window handles (HWND)

Uses ctypes to call user32.dll directly. Automatically selects the correct
GetWindowLong/SetWindowLong variant for 32-bit vs 64-bit Python.
"""

import sys
import ctypes
from ctypes import wintypes


# ---------------------------------------------------------------------------
# user32.dll handle
# ---------------------------------------------------------------------------

user32 = ctypes.windll.user32

# ---------------------------------------------------------------------------
# Window style constants
# ---------------------------------------------------------------------------

GWL_STYLE: int = -16
WS_CHILD: int = 0x40000000
WS_POPUP: int = 0x80000000

# ---------------------------------------------------------------------------
# 32-bit vs 64-bit: select the correct Get/SetWindowLong variant
# ---------------------------------------------------------------------------
# On 64-bit Windows, GetWindowLongW/SetWindowLongW truncate pointer-sized
# values. The *PtrW variants handle the full 64-bit range.
# ---------------------------------------------------------------------------

if sys.maxsize > 2**32:
    GetWindowLong = user32.GetWindowLongPtrW
    SetWindowLong = user32.SetWindowLongPtrW
else:
    GetWindowLong = user32.GetWindowLongW
    SetWindowLong = user32.SetWindowLongW

# ---------------------------------------------------------------------------
# argtypes / restype declarations
# ---------------------------------------------------------------------------

# GetWindowLong / SetWindowLong
GetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int]
GetWindowLong.restype = ctypes.c_void_p

SetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
SetWindowLong.restype = ctypes.c_void_p

# FindWindowExW – uses c_void_p instead of HWND so NULL (0) can be passed
# safely without ctypes raising an ArgumentError.
user32.FindWindowExW.argtypes = [
    ctypes.c_void_p,   # hWndParent  (0 = desktop)
    ctypes.c_void_p,   # hWndChildAfter
    wintypes.LPCWSTR,  # lpszClass
    wintypes.LPCWSTR,  # lpszWindow
]
user32.FindWindowExW.restype = ctypes.c_void_p

# IsWindow – validates whether an HWND still refers to a live window.
user32.IsWindow.argtypes = [ctypes.c_void_p]
user32.IsWindow.restype = ctypes.c_int

# GetClientRect – retrieves the client-area dimensions.
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.restype = wintypes.BOOL

# GetWindowRect – retrieves the bounding rectangle in screen coordinates.
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL

# SetParent – changes the parent window of a child window.
user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
user32.SetParent.restype = wintypes.HWND

# FindWindowW – finds a top-level window by class name and/or title.
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND


# ---------------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------------

def find_all_taskbars() -> list[tuple[str, int]]:
    """Find all Windows taskbars across all monitors.

    Returns a list of ``(name, hwnd)`` tuples where *name* is a
    human-readable screen label (``'Screen 1'``, ``'Screen 2'``, …) and
    *hwnd* is the native window handle of the corresponding taskbar.

    The primary taskbar is discovered via the ``Shell_TrayWnd`` window
    class.  Secondary taskbars (one per additional monitor) use the
    ``Shell_SecondaryTrayWnd`` class and are enumerated with
    ``FindWindowExW``.
    """
    taskbars: list[tuple[str, int]] = []

    try:
        # Primary taskbar
        primary = user32.FindWindowW("Shell_TrayWnd", None)
        if primary:
            taskbars.append(("Screen 1", int(primary)))

        # Secondary taskbars (multi-monitor setups)
        prev_hwnd: int = 0
        screen_index: int = 2
        while True:
            hwnd = user32.FindWindowExW(
                0, prev_hwnd, "Shell_SecondaryTrayWnd", None
            )
            if not hwnd:
                break
            taskbars.append((f"Screen {screen_index}", int(hwnd)))
            prev_hwnd = hwnd
            screen_index += 1
    except OSError:
        pass

    return taskbars


def inject_into_taskbar(widget_hwnd: int, taskbar_hwnd: int) -> bool:
    """Inject a widget window into a taskbar as a child window.

    This performs two operations:

    1. ``SetParent`` – reparents *widget_hwnd* under *taskbar_hwnd*.
    2. Style update – adds ``WS_CHILD`` and removes ``WS_POPUP`` so the
       window behaves as a proper child of the taskbar.

    Args:
        widget_hwnd: The native window handle of the widget to inject.
        taskbar_hwnd: The native window handle of the target taskbar.

    Returns:
        ``True`` if the injection succeeded, ``False`` otherwise.
    """
    try:
        user32.SetParent(widget_hwnd, taskbar_hwnd)

        style = GetWindowLong(widget_hwnd, GWL_STYLE)
        if style is not None:
            style_int = int(style)
            new_style = (style_int | WS_CHILD) & ~WS_POPUP
            SetWindowLong(widget_hwnd, GWL_STYLE, new_style)

        return True
    except OSError:
        return False


def is_window_valid(hwnd: int) -> bool:
    """Check whether *hwnd* refers to an existing window.

    Thin wrapper around the Win32 ``IsWindow`` function.  Useful for
    detecting monitor disconnects or taskbar restarts.

    Args:
        hwnd: The native window handle to validate.

    Returns:
        ``True`` if the window exists, ``False`` otherwise.
    """
    return bool(user32.IsWindow(hwnd))


def get_taskbar_rect(hwnd: int) -> tuple[int, int]:
    """Return the client-area dimensions of a taskbar.

    Args:
        hwnd: The native window handle of the taskbar.

    Returns:
        A ``(width, height)`` tuple representing the client rectangle.
    """
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    return (rect.right - rect.left, rect.bottom - rect.top)


def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    """Return the bounding rectangle of a window in screen coordinates.

    Args:
        hwnd: The native window handle.

    Returns:
        A ``(left, top, right, bottom)`` tuple.
    """
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)
