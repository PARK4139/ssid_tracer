import ctypes
import argparse
import os
import sys
import threading
import time
from ctypes import wintypes

from ssid_config import ENABLE_ANSI_COLOR, WATCH_INTERVAL_SEC
from ssid_analyzer import (
    EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY,
    EVER_LIVE_CONFIRMED_SSID_BAND_SET,
    get_check_result,
    get_trace_verdict,
    get_trace_verdict_text,
)
from ssid_renderer import DISPLAY_SECTIONS, build_result_screen, get_rich_console, print_result
from ssid_renderer_result import print_trace_verdict
from ssid_scanner import get_detected_wifi_entries_with_retry
from ssid_utils import (
    get_band_from_channel,
    get_unique_expected_2_4g_ssids,
    get_unique_expected_5g_ssids,
    get_unique_ignored_ssids,
    get_unique_planned_ssids,
)


def setup_console_drag():
    if os.name != "nt":
        return

    WM_NCLBUTTONDOWN = 0x00A1
    HTCAPTION = 2
    GA_ROOT = 2

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = kernel32.GetConsoleWindow()
    if not hwnd:
        return

    def _drag_loop():
        prev = False
        while True:
            pressed = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
            if pressed and not prev:
                pt = wintypes.POINT()
                user32.GetCursorPos(ctypes.byref(pt))
                window_at = user32.WindowFromPoint(pt)
                root = user32.GetAncestor(window_at, GA_ROOT)
                if root == hwnd:
                    user32.ReleaseCapture()
                    user32.PostMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)
            prev = pressed
            time.sleep(0.01)

    threading.Thread(target=_drag_loop, daemon=True).start()


def ensure_ansi_color_enabled():
    if not ENABLE_ANSI_COLOR:
        return

    if os.name != "nt":
        return

    try:
        kernel32 = ctypes.windll.kernel32
        stdout_handle = kernel32.GetStdHandle(-11)
        mode = wintypes.DWORD()

        if kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode)) == 0:
            return

        kernel32.SetConsoleMode(stdout_handle, mode.value | 0x0004)

    except Exception:
        return


def clear_console():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def ensure_wifi_expected_ssids_watched(section_name="all"):
    ensure_ansi_color_enabled()
    setup_console_drag()

    expected_5g_ssids = get_unique_expected_5g_ssids()
    expected_2_4g_ssids = get_unique_expected_2_4g_ssids()
    ignored_ssids = get_unique_ignored_ssids()
    planned_ssids = get_unique_planned_ssids()

    if len(expected_5g_ssids) <= 0 and len(expected_2_4g_ssids) <= 0:
        print("No expected SSID defined")
        sys.exit(1)

    console = get_rich_console()

    while True:
        loop_started_at = time.time()

        detected_wifi_entries, scan_ok, scan_message, error_message = get_detected_wifi_entries_with_retry()
        clear_console()
        console.print(
            build_result_screen(
                expected_5g_ssids=expected_5g_ssids,
                expected_2_4g_ssids=expected_2_4g_ssids,
                ignored_ssids=ignored_ssids,
                planned_ssids=planned_ssids,
                detected_wifi_entries=detected_wifi_entries,
                scan_ok=scan_ok,
                scan_message=scan_message,
                error_message=error_message,
                section_name=section_name,
            )
        )

        elapsed_sec = time.time() - loop_started_at
        sleep_sec = max(0.0, WATCH_INTERVAL_SEC - elapsed_sec)
        time.sleep(sleep_sec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--section",
        choices=DISPLAY_SECTIONS,
        default="all",
    )
    args = parser.parse_args()
    ensure_wifi_expected_ssids_watched(section_name=args.section)


if __name__ == "__main__":
    main()
