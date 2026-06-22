import ctypes
import argparse
import os
import sys
import threading
import time
from ctypes import wintypes

from ssid_config import (
    ENABLE_ANSI_COLOR,
    SELECTED_SSID_CONFIG_PATH,
    SKIP_TBD,
    SSID_CONFIGS,
    WATCH_INTERVAL_SEC,
)
from ssid_analyzer import (
    EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY,
    EVER_LIVE_CONFIRMED_SSID_BAND_SET,
    get_check_result,
    get_trace_verdict,
    get_trace_verdict_text,
)
from ssid_renderer import DISPLAY_SECTIONS, build_result_screen, get_rich_console, print_result
from ssid_renderer_result import build_not_tested_result_section, print_trace_verdict
from ssid_scanner import get_detected_wifi_entries_with_retry
from ssid_utils import (
    ensure_selected_ssid_config_name_written,
    get_band_from_channel,
    get_available_ssid_config_names,
    get_completed_ssid_config_name,
    get_ssid_config_by_name,
    get_unique_ssids,
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


def ensure_value_completed(value, choices, prompt_message):
    if value in choices:
        return value

    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.completion import FuzzyWordCompleter

        completed_value = prompt(
            prompt_message,
            completer=FuzzyWordCompleter(words=choices),
            complete_while_typing=True,
        ).strip()
    except (EOFError, KeyboardInterrupt):
        raise
    except Exception:
        print(prompt_message)
        for index, choice in enumerate(choices, start=1):
            print(f"  {index}. {choice}")
        completed_value = input("> ").strip()

    if completed_value in choices:
        return completed_value

    if completed_value.isdigit():
        selected_index = int(completed_value) - 1
        if 0 <= selected_index < len(choices):
            return choices[selected_index]

    return choices[0]


def ensure_ssid_config_selected_interactively():
    selected_ssid_config_name = ensure_value_completed(
        value=None,
        choices=get_available_ssid_config_names(),
        prompt_message="Config> ",
    )
    return ensure_selected_ssid_config_name_written(ssid_config_name=selected_ssid_config_name)


def get_raw_selected_ssid_config_name():
    if not SELECTED_SSID_CONFIG_PATH.exists():
        return None

    selected_ssid_config_name = SELECTED_SSID_CONFIG_PATH.read_text(encoding="utf-8").strip()
    if selected_ssid_config_name not in SSID_CONFIGS:
        return None

    return selected_ssid_config_name


def get_current_ssid_configuration():
    config_name = get_raw_selected_ssid_config_name()
    if config_name is None:
        return {
            "config_name": None,
            "expected_5g_ssids": [],
            "expected_2_4g_ssids": [],
            "ignored_ssids": [],
            "planned_ssids": [],
        }

    config_name = get_completed_ssid_config_name(ssid_config_name=config_name)
    selected_ssid_config = get_ssid_config_by_name(ssid_config_name=config_name)
    return {
        "config_name": config_name,
        "expected_5g_ssids": get_unique_ssids(raw_ssids=selected_ssid_config["expected_5g_ssids"], skip_tbd=SKIP_TBD),
        "expected_2_4g_ssids": get_unique_ssids(raw_ssids=selected_ssid_config["expected_2_4g_ssids"], skip_tbd=SKIP_TBD),
        "ignored_ssids": get_unique_ssids(raw_ssids=selected_ssid_config["ignored_ssids"], skip_tbd=True),
        "planned_ssids": get_unique_ssids(raw_ssids=selected_ssid_config["planned_ssids"], skip_tbd=True),
    }


def print_current_result_screen(console, current_ssid_configuration, detected_wifi_entries, scan_ok, scan_message, error_message, section_name):
    clear_console()
    if current_ssid_configuration["config_name"] is None:
        console.print(build_not_tested_result_section())
        return

    console.print(
        build_result_screen(
            config_name=current_ssid_configuration["config_name"],
            expected_5g_ssids=current_ssid_configuration["expected_5g_ssids"],
            expected_2_4g_ssids=current_ssid_configuration["expected_2_4g_ssids"],
            ignored_ssids=current_ssid_configuration["ignored_ssids"],
            planned_ssids=current_ssid_configuration["planned_ssids"],
            detected_wifi_entries=detected_wifi_entries,
            scan_ok=scan_ok,
            scan_message=scan_message,
            error_message=error_message,
            section_name=section_name,
        )
    )


def ensure_wifi_expected_ssids_watched(section_name="all"):
    ensure_ansi_color_enabled()
    setup_console_drag()

    if section_name == "config":
        ensure_ssid_config_selected_interactively()

    console = get_rich_console()
    current_ssid_configuration = get_current_ssid_configuration()

    print_current_result_screen(
        console=console,
        current_ssid_configuration=current_ssid_configuration,
        detected_wifi_entries=[],
        scan_ok=False,
        scan_message="scan pending",
        error_message="",
        section_name=section_name,
    )

    while True:
        loop_started_at = time.time()
        current_ssid_configuration = get_current_ssid_configuration()

        if current_ssid_configuration["config_name"] is None:
            print_current_result_screen(
                console=console,
                current_ssid_configuration=current_ssid_configuration,
                detected_wifi_entries=[],
                scan_ok=False,
                scan_message="config not selected",
                error_message="",
                section_name=section_name,
            )
            elapsed_sec = time.time() - loop_started_at
            sleep_sec = max(0.0, WATCH_INTERVAL_SEC - elapsed_sec)
            time.sleep(sleep_sec)
            continue

        if len(current_ssid_configuration["expected_5g_ssids"]) <= 0 and len(current_ssid_configuration["expected_2_4g_ssids"]) <= 0:
            print("No expected SSID defined")
            sys.exit(1)

        detected_wifi_entries, scan_ok, scan_message, error_message = get_detected_wifi_entries_with_retry()
        print_current_result_screen(
            console=console,
            current_ssid_configuration=current_ssid_configuration,
            detected_wifi_entries=detected_wifi_entries,
            scan_ok=scan_ok,
            scan_message=scan_message,
            error_message=error_message,
            section_name=section_name,
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
