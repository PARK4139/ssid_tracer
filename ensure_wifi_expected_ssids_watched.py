import ctypes
import os
import re
import subprocess
import sys
import time
from ctypes import wintypes

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


EXPECTED_5G_SSIDS_RAW = [
    "MERCUSYS_BA30_5G",
    "ASUS_F6",
    "NETGEAR11-5G",
    "NETGEAR56-5G",
    "Tenda_EFFAA0_5G",
    "TP-Link_A2B2_5G",
    "TP-Link_35E8_5G",
    "rd28_minet_11fc",
    "Keenetic-1947",
    "WLAN-Funknetz",
    "TP-Link_5GHz_138BD2",
    "TP-Link_3B54_5G",
    "ASUS_00_EBR63",
    "ASUS_C8",
    "ASUS_60",
    "Tenda_EFE220_5G",
    "MERCUSYS_77AC_5G",
    "rd28_minet_131e",
    "Linksys00711",
    "Cuby-A254-5G",
    "_LinksysSetup99A",
    "R15-FEFA",
    "TBD",
    "TP-Link_EB98_5G",
    "TP-Link_9B40_5G",
    "reliability1_5G",
    "MERCUSYS_C027_5G",
    "TP-Link_8A5C_5G",
    "TP-Link_E8E4_5G",
    "#6_5G",
    "huvitz2",
]


EXPECTED_2_4G_SSIDS_RAW = [
    "MERCUSYS_BA30",
    "ASUS_F6",
    "NETGEAR11",
    "NETGEAR56",
    "Tenda_EFFAA0",
    "TP-Link_A2B2",
    "TP-Link_35E8",
    "rd28_minet_11fc",
    "Keenetic-1947",
    "WLAN-Funknetz",
    "TP-Link_2.4GHz_138BD1",
    "TP-Link_3B54",
    "ASUS_00_EBR63",
    "ASUS_C8",
    "ASUS_60",
    "Tenda_EFE220",
    "MERCUSYS_77AC",
    "rd28_minet_131e",
    "Linksys00711",
    "Cuby-A254",
    "_LinksysSetup99A",
    "R15-FEFA",
    "TBD",
    "TP-Link_EB98",
    "TP-Link_9B40",
    "reliability1",
    "MERCUSYS_C027",
    "TP-Link_8A5C",
    "TP-Link_E8E4",
    "#6",
    "huvitz2",
]


IGNORED_SSIDS_RAW = [
    "Huvitz",
    "Huvitz-Guest",
    "DIRECT-70 SL-C1615W",
    "NETGEAR90-5G",
    "NETGEAR90",
    "하니부",
]


WATCH_INTERVAL_SEC = 0.25
SCAN_SETTLE_SEC = 0.15
NETSH_RETRY_COUNT = 2
NETSH_RETRY_SETTLE_SEC = 0.05

PLANNED_SSIDS_RAW = [
    "Linksys00711",
    "Cuby-A254-5G",
    "Cuby-A254",
    "_LinksysSetup99A",
    "R15-FEFA",
]

SKIP_TBD = True
CASE_SENSITIVE = True
SHOW_ALL_DETECTED_WIFI_ENTRIES = True
SHOW_IGNORED_SSIDS = True
SORT_OUTPUT_ASCENDING = True
ENABLE_ANSI_COLOR = True

ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_GRAY = "\033[90m"
ANSI_ORANGE = "\033[38;5;208m"
ANSI_RESET = "\033[0m"

EVER_LIVE_CONFIRMED_SSID_BAND_SET = set()
EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY = {}


def get_rich_console():
    return Console(
        no_color=not ENABLE_ANSI_COLOR,
    )


def get_rich_style(color_name):
    style_by_color_name = {
        "green": "green",
        "gray": "bright_black",
        "red": "red",
        "orange": "orange3",
    }

    return style_by_color_name.get(
        color_name,
        "",
    )


def build_rich_section(title, renderables, border_style="white"):
    if len(renderables) <= 0:
        renderables = [
            Text("  -"),
        ]

    return Panel(
        Group(*renderables),
        title=title,
        border_style=border_style,
        box=box.ASCII,
    )


def print_rich_section(title, renderables, border_style="white"):
    get_rich_console().print(
        build_rich_section(
            title=title,
            renderables=renderables,
            border_style=border_style,
        )
    )


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


class WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [
        ("InterfaceGuid", GUID),
        ("strInterfaceDescription", wintypes.WCHAR * 256),
        ("isState", wintypes.DWORD),
    ]


class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
    _fields_ = [
        ("dwNumberOfItems", wintypes.DWORD),
        ("dwIndex", wintypes.DWORD),
        ("InterfaceInfo", WLAN_INTERFACE_INFO * 1),
    ]


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

        enable_virtual_terminal_processing = 0x0004

        kernel32.SetConsoleMode(
            stdout_handle,
            mode.value | enable_virtual_terminal_processing,
        )

    except Exception:
        return


def get_red_text(text):
    if not ENABLE_ANSI_COLOR:
        return text

    return f"{ANSI_RED}{text}{ANSI_RESET}"


def get_green_text(text):
    if not ENABLE_ANSI_COLOR:
        return text

    return f"{ANSI_GREEN}{text}{ANSI_RESET}"


def get_gray_text(text):
    if not ENABLE_ANSI_COLOR:
        return text

    return f"{ANSI_GRAY}{text}{ANSI_RESET}"


def get_orange_text(text):
    if not ENABLE_ANSI_COLOR:
        return text

    return f"{ANSI_ORANGE}{text}{ANSI_RESET}"


def get_colored_text(text, color_name):
    if color_name == "green":
        return get_green_text(text)
    if color_name == "gray":
        return get_gray_text(text)
    if color_name == "red":
        return get_red_text(text)
    if color_name == "orange":
        return get_orange_text(text)

    return text


def normalize_ssid_for_compare(ssid):
    if CASE_SENSITIVE:
        return ssid

    return ssid.lower()


def get_sort_key(value):
    return str(value).casefold()


def get_wifi_entry_sort_key(wifi_entry):
    return (
        get_sort_key(
            value=wifi_entry.get("ssid", ""),
        ),
        get_sort_key(
            value=wifi_entry.get("band", ""),
        ),
        int(wifi_entry.get("channel", 0) or 0),
    )


def get_sorted_ssids(ssids):
    if not SORT_OUTPUT_ASCENDING:
        return list(ssids)

    return sorted(
        ssids,
        key=get_sort_key,
    )


def get_sorted_wifi_entries(wifi_entries):
    if not SORT_OUTPUT_ASCENDING:
        return list(wifi_entries)

    return sorted(
        wifi_entries,
        key=get_wifi_entry_sort_key,
    )


def get_unique_ssids(raw_ssids, skip_tbd):
    unique_ssids = []
    seen = set()

    for ssid in raw_ssids:
        normalized_ssid = ssid.strip()

        if normalized_ssid == "":
            continue

        if skip_tbd and normalized_ssid.upper() == "TBD":
            continue

        comparable_ssid = normalize_ssid_for_compare(
            ssid=normalized_ssid,
        )

        if comparable_ssid in seen:
            continue

        seen.add(comparable_ssid)
        unique_ssids.append(normalized_ssid)

    return unique_ssids


def get_unique_expected_5g_ssids():
    return get_unique_ssids(
        raw_ssids=EXPECTED_5G_SSIDS_RAW,
        skip_tbd=SKIP_TBD,
    )


def get_unique_expected_2_4g_ssids():
    return get_unique_ssids(
        raw_ssids=EXPECTED_2_4G_SSIDS_RAW,
        skip_tbd=SKIP_TBD,
    )


def get_unique_ignored_ssids():
    return get_unique_ssids(
        raw_ssids=IGNORED_SSIDS_RAW,
        skip_tbd=True,
    )


def get_unique_planned_ssids():
    return get_unique_ssids(
        raw_ssids=PLANNED_SSIDS_RAW,
        skip_tbd=True,
    )


def get_band_from_channel(channel):
    if channel is None:
        return "UNKNOWN"

    if 1 <= channel <= 14:
        return "2_4G"

    if channel >= 32:
        return "5G"

    return "UNKNOWN"


def get_grouped_wifi_entries_by_ssid_and_band(wifi_entries):
    grouped_by_key = {}

    for wifi_entry in wifi_entries:
        ssid = wifi_entry.get("ssid", "")
        band = wifi_entry.get("band", "UNKNOWN")
        channel = wifi_entry.get("channel", "")
        bssid = wifi_entry.get("bssid", "")

        comparable_ssid = normalize_ssid_for_compare(
            ssid=ssid,
        )

        group_key = (
            comparable_ssid,
            band,
        )

        if group_key not in grouped_by_key:
            grouped_by_key[group_key] = {
                "ssid": ssid,
                "band": band,
                "channels": set(),
                "bssids": set(),
            }

        if channel != "":
            grouped_by_key[group_key]["channels"].add(channel)

        if bssid != "":
            grouped_by_key[group_key]["bssids"].add(bssid)

    grouped_wifi_entries = []

    for grouped_entry in grouped_by_key.values():
        channels = sorted(
            grouped_entry["channels"],
            key=lambda value: int(value),
        )

        bssids = sorted(
            grouped_entry["bssids"],
            key=get_sort_key,
        )

        grouped_wifi_entries.append(
            {
                "ssid": grouped_entry["ssid"],
                "band": grouped_entry["band"],
                "channels": channels,
                "bssids": bssids,
                "bssid_count": len(bssids),
            }
        )

    if not SORT_OUTPUT_ASCENDING:
        return grouped_wifi_entries

    return sorted(
        grouped_wifi_entries,
        key=lambda item: (
            get_sort_key(
                value=item.get("ssid", ""),
            ),
            get_sort_key(
                value=item.get("band", ""),
            ),
        ),
    )


def ensure_wlan_scan_requested():
    try:
        wlanapi = ctypes.WinDLL("wlanapi.dll")

        WlanOpenHandle = wlanapi.WlanOpenHandle
        WlanOpenHandle.argtypes = [
            wintypes.DWORD,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.HANDLE),
        ]
        WlanOpenHandle.restype = wintypes.DWORD

        WlanEnumInterfaces = wlanapi.WlanEnumInterfaces
        WlanEnumInterfaces.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            ctypes.POINTER(ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)),
        ]
        WlanEnumInterfaces.restype = wintypes.DWORD

        WlanScan = wlanapi.WlanScan
        WlanScan.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(GUID),
            wintypes.LPVOID,
            wintypes.LPVOID,
            wintypes.LPVOID,
        ]
        WlanScan.restype = wintypes.DWORD

        WlanFreeMemory = wlanapi.WlanFreeMemory
        WlanFreeMemory.argtypes = [
            wintypes.LPVOID,
        ]
        WlanFreeMemory.restype = None

        WlanCloseHandle = wlanapi.WlanCloseHandle
        WlanCloseHandle.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
        ]
        WlanCloseHandle.restype = wintypes.DWORD

        negotiated_version = wintypes.DWORD()
        client_handle = wintypes.HANDLE()

        result = WlanOpenHandle(
            wintypes.DWORD(2),
            None,
            ctypes.byref(negotiated_version),
            ctypes.byref(client_handle),
        )

        if result != 0:
            return False, f"WlanOpenHandle failed: {result}"

        interface_list_pointer = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()

        try:
            result = WlanEnumInterfaces(
                client_handle,
                None,
                ctypes.byref(interface_list_pointer),
            )

            if result != 0:
                return False, f"WlanEnumInterfaces failed: {result}"

            interface_count = interface_list_pointer.contents.dwNumberOfItems

            if interface_count <= 0:
                return False, "No WLAN interface found"

            first_interface_address = ctypes.addressof(
                interface_list_pointer.contents.InterfaceInfo
            )
            interface_size = ctypes.sizeof(
                WLAN_INTERFACE_INFO,
            )

            scan_requested_count = 0
            scan_failed_count = 0

            for index in range(interface_count):
                interface_info = WLAN_INTERFACE_INFO.from_address(
                    first_interface_address + index * interface_size
                )

                result = WlanScan(
                    client_handle,
                    ctypes.byref(interface_info.InterfaceGuid),
                    None,
                    None,
                    None,
                )

                if result == 0:
                    scan_requested_count += 1
                else:
                    scan_failed_count += 1

            if scan_requested_count <= 0:
                return False, f"WlanScan failed for all interfaces: failed={scan_failed_count}"

            return True, f"WlanScan requested: ok={scan_requested_count}, failed={scan_failed_count}"

        finally:
            if interface_list_pointer:
                WlanFreeMemory(
                    interface_list_pointer,
                )

            WlanCloseHandle(
                client_handle,
                None,
            )

    except Exception as exception:
        return False, f"WlanScan exception: {exception}"


def get_decoded_text(raw_bytes):
    for encoding in [
        "cp949",
        "utf-8",
        "utf-16",
    ]:
        try:
            return raw_bytes.decode(
                encoding=encoding,
                errors="strict",
            )
        except UnicodeDecodeError:
            continue

    return raw_bytes.decode(
        encoding="cp949",
        errors="replace",
    )


def get_netsh_output():
    completed_process = subprocess.run(
        [
            "netsh",
            "wlan",
            "show",
            "networks",
            "mode=bssid",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )

    stdout_text = get_decoded_text(
        raw_bytes=completed_process.stdout,
    )
    stderr_text = get_decoded_text(
        raw_bytes=completed_process.stderr,
    )

    return completed_process.returncode, stdout_text, stderr_text


def get_detected_wifi_entries_once():
    returncode, stdout_text, stderr_text = get_netsh_output()

    if returncode != 0:
        return [], f"netsh failed: {stderr_text.strip()}"

    detected_wifi_entries = []
    current_ssid = None
    current_bssid = None

    for line in stdout_text.splitlines():
        stripped_line = line.strip()

        ssid_match = re.match(
            pattern=r"^SSID\s+\d+\s*:\s*(.*)$",
            string=stripped_line,
        )

        if ssid_match is not None:
            current_ssid = ssid_match.group(1).strip()
            current_bssid = None
            continue

        bssid_match = re.match(
            pattern=r"^BSSID\s+\d+\s*:\s*(.*)$",
            string=stripped_line,
            flags=re.IGNORECASE,
        )

        if bssid_match is not None:
            current_bssid = bssid_match.group(1).strip()
            continue

        channel_match = re.match(
            pattern=r"^(Channel|채널)\s*:\s*(\d+)\s*$",
            string=stripped_line,
            flags=re.IGNORECASE,
        )

        if channel_match is None:
            continue

        if current_ssid is None or current_ssid == "":
            continue

        channel = int(channel_match.group(2))
        band = get_band_from_channel(
            channel=channel,
        )

        detected_wifi_entries.append(
            {
                "ssid": current_ssid,
                "bssid": current_bssid or "",
                "channel": channel,
                "band": band,
            }
        )

    return detected_wifi_entries, ""


def get_detected_wifi_entries_with_retry():
    last_scan_ok = False
    last_scan_message = ""
    last_error_message = ""

    for attempt_index in range(NETSH_RETRY_COUNT + 1):
        scan_ok, scan_message = ensure_wlan_scan_requested()

        last_scan_ok = scan_ok
        last_scan_message = scan_message

        time.sleep(
            SCAN_SETTLE_SEC,
        )

        detected_wifi_entries, error_message = get_detected_wifi_entries_once()

        if len(detected_wifi_entries) > 0:
            return detected_wifi_entries, scan_ok, scan_message, ""

        last_error_message = error_message

        time.sleep(
            NETSH_RETRY_SETTLE_SEC,
        )

    return [], last_scan_ok, last_scan_message, last_error_message


def get_detected_ssid_band_set(detected_wifi_entries):
    detected_ssid_band_set = set()

    for wifi_entry in detected_wifi_entries:
        comparable_ssid = normalize_ssid_for_compare(
            ssid=wifi_entry.get("ssid", ""),
        )
        band = wifi_entry.get("band", "UNKNOWN")

        detected_ssid_band_set.add(
            (
                comparable_ssid,
                band,
            )
        )

    return detected_ssid_band_set


def get_wifi_group_key(ssid, band):
    return (
        normalize_ssid_for_compare(
            ssid=ssid,
        ),
        band,
    )


def get_expected_ssid_band_set(expected_5g_ssids, expected_2_4g_ssids):
    expected_ssid_band_set = set()

    for ssid in expected_5g_ssids:
        expected_ssid_band_set.add(
            (
                normalize_ssid_for_compare(
                    ssid=ssid,
                ),
                "5G",
            )
        )

    for ssid in expected_2_4g_ssids:
        expected_ssid_band_set.add(
            (
                normalize_ssid_for_compare(
                    ssid=ssid,
                ),
                "2_4G",
            )
        )

    return expected_ssid_band_set


def get_check_result(expected_5g_ssids, expected_2_4g_ssids, ignored_ssids, detected_wifi_entries):
    global EVER_LIVE_CONFIRMED_SSID_BAND_SET
    global EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY

    expected_ssid_band_set = get_expected_ssid_band_set(
        expected_5g_ssids=expected_5g_ssids,
        expected_2_4g_ssids=expected_2_4g_ssids,
    )

    ignored_set = {
        normalize_ssid_for_compare(
            ssid=ssid,
        )
        for ssid in ignored_ssids
    }

    detected_ssid_band_set = get_detected_ssid_band_set(
        detected_wifi_entries=detected_wifi_entries,
    )
    grouped_detected_wifi_entries = get_grouped_wifi_entries_by_ssid_and_band(
        wifi_entries=detected_wifi_entries,
    )
    current_detected_wifi_group_keys = set()

    for grouped_wifi_entry in grouped_detected_wifi_entries:
        group_key = get_wifi_group_key(
            ssid=grouped_wifi_entry.get("ssid", ""),
            band=grouped_wifi_entry.get("band", "UNKNOWN"),
        )
        current_detected_wifi_group_keys.add(
            group_key,
        )
        EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY[group_key] = grouped_wifi_entry

    grouped_detected_wifi_entry_by_group_key = {
        get_wifi_group_key(
            ssid=grouped_wifi_entry.get("ssid", ""),
            band=grouped_wifi_entry.get("band", "UNKNOWN"),
        ): grouped_wifi_entry
        for grouped_wifi_entry in grouped_detected_wifi_entries
    }

    live_confirmed_5g_ssids = []
    live_confirmed_2_4g_ssids = []
    dead_confirmed_5g_ssids = []
    dead_confirmed_2_4g_ssids = []
    dead_detected_wifi_entries = []
    missing_5g_ssids = []
    missing_2_4g_ssids = []

    current_live_confirmed_set = expected_ssid_band_set.intersection(
        detected_ssid_band_set,
    )

    EVER_LIVE_CONFIRMED_SSID_BAND_SET.update(
        current_live_confirmed_set,
    )

    for expected_ssid in expected_5g_ssids:
        comparable_expected_ssid = normalize_ssid_for_compare(
            ssid=expected_ssid,
        )
        expected_key = (
            comparable_expected_ssid,
            "5G",
        )

        if expected_key in detected_ssid_band_set:
            live_confirmed_5g_ssids.append(
                grouped_detected_wifi_entry_by_group_key.get(
                    expected_key,
                    {
                        "ssid": expected_ssid,
                        "band": "5G",
                        "channels": [],
                        "bssids": [],
                        "bssid_count": 0,
                    },
                )
            )
        elif expected_key in EVER_LIVE_CONFIRMED_SSID_BAND_SET:
            dead_confirmed_5g_ssids.append(
                expected_ssid,
            )
        else:
            missing_5g_ssids.append(
                expected_ssid,
            )

    for expected_ssid in expected_2_4g_ssids:
        comparable_expected_ssid = normalize_ssid_for_compare(
            ssid=expected_ssid,
        )
        expected_key = (
            comparable_expected_ssid,
            "2_4G",
        )

        if expected_key in detected_ssid_band_set:
            live_confirmed_2_4g_ssids.append(
                grouped_detected_wifi_entry_by_group_key.get(
                    expected_key,
                    {
                        "ssid": expected_ssid,
                        "band": "2_4G",
                        "channels": [],
                        "bssids": [],
                        "bssid_count": 0,
                    },
                )
            )
        elif expected_key in EVER_LIVE_CONFIRMED_SSID_BAND_SET:
            dead_confirmed_2_4g_ssids.append(
                expected_ssid,
            )
        else:
            missing_2_4g_ssids.append(
                expected_ssid,
            )

    ignored_detected_wifi_entries = []
    not_confirmed_wifi_entries = []

    seen_ignored_entry_keys = set()
    seen_not_confirmed_entry_keys = set()

    for wifi_entry in detected_wifi_entries:
        ssid = wifi_entry.get("ssid", "")
        channel = wifi_entry.get("channel", 0)
        band = wifi_entry.get("band", "UNKNOWN")
        bssid = wifi_entry.get("bssid", "")

        comparable_ssid = normalize_ssid_for_compare(
            ssid=ssid,
        )

        wifi_entry_key = (
            comparable_ssid,
            band,
            channel,
            bssid,
        )

        if comparable_ssid in ignored_set:
            if wifi_entry_key not in seen_ignored_entry_keys:
                ignored_detected_wifi_entries.append(
                    wifi_entry,
                )
                seen_ignored_entry_keys.add(
                    wifi_entry_key,
                )
            continue

        if (comparable_ssid, band) not in expected_ssid_band_set:
            if wifi_entry_key not in seen_not_confirmed_entry_keys:
                not_confirmed_wifi_entries.append(
                    wifi_entry,
                )
                seen_not_confirmed_entry_keys.add(
                    wifi_entry_key,
                )

    action_required_items = []

    for ssid in missing_5g_ssids:
        action_required_items.append(
            {
                "status_label": "MISSING_5G",
                "ssid": ssid,
                "band": "5G",
                "channel": "",
                "reason": "Expected 5GHz SSID has never been detected",
            }
        )

    for ssid in missing_2_4g_ssids:
        action_required_items.append(
            {
                "status_label": "MISSING_2_4G",
                "ssid": ssid,
                "band": "2_4G",
                "channel": "",
                "reason": "Expected 2.4GHz SSID has never been detected",
            }
        )

    grouped_not_confirmed_wifi_entries = get_grouped_wifi_entries_by_ssid_and_band(
        wifi_entries=not_confirmed_wifi_entries,
    )

    for wifi_entry in grouped_not_confirmed_wifi_entries:
        band = wifi_entry.get("band", "UNKNOWN")
        channels_text = ", ".join(
            str(channel)
            for channel in wifi_entry.get("channels", [])
        )

        if channels_text == "":
            channels_text = "-"

        if band == "5G":
            status_label = "NOT_CONFIRMED_5G"
            reason = "Detected 5GHz SSID but not in expected 5GHz list"
        elif band == "2_4G":
            status_label = "NOT_CONFIRMED_2_4G"
            reason = "Detected 2.4GHz SSID but not in expected 2.4GHz list"
        else:
            status_label = "NOT_CONFIRMED_UNKNOWN"
            reason = "Detected SSID with unknown band"

        action_required_items.append(
            {
                "status_label": status_label,
                "ssid": wifi_entry.get("ssid", ""),
                "band": band,
                "channel": channels_text,
                "reason": f"{reason}; bssid_count={wifi_entry.get('bssid_count', 0)}",
            }
        )

    live_confirmed_5g_ssids = get_sorted_wifi_entries(
        wifi_entries=live_confirmed_5g_ssids,
    )
    live_confirmed_2_4g_ssids = get_sorted_wifi_entries(
        wifi_entries=live_confirmed_2_4g_ssids,
    )
    dead_confirmed_5g_ssids = get_sorted_ssids(
        ssids=dead_confirmed_5g_ssids,
    )
    dead_confirmed_2_4g_ssids = get_sorted_ssids(
        ssids=dead_confirmed_2_4g_ssids,
    )
    ignored_detected_wifi_entries = get_sorted_wifi_entries(
        wifi_entries=ignored_detected_wifi_entries,
    )
    dead_detected_wifi_entries = get_sorted_wifi_entries(
        wifi_entries=[
            wifi_entry
            for group_key, wifi_entry in EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY.items()
            if group_key not in current_detected_wifi_group_keys
            and group_key not in expected_ssid_band_set
        ],
    )

    action_required_items = sorted(
        action_required_items,
        key=lambda item: (
            get_sort_key(
                value=item["ssid"],
            ),
            get_sort_key(
                value=item["status_label"],
            ),
            get_sort_key(
                value=item.get("channel", ""),
            ),
        ),
    )

    return (
        live_confirmed_5g_ssids,
        live_confirmed_2_4g_ssids,
        dead_confirmed_5g_ssids,
        dead_confirmed_2_4g_ssids,
        dead_detected_wifi_entries,
        action_required_items,
        ignored_detected_wifi_entries,
    )


def get_action_required_ssids_by_status(action_required_items, status_label):
    return [
        item.get("ssid", "")
        for item in action_required_items
        if item.get("status_label", "") == status_label
    ]


def get_action_required_ssid_channel_text_by_status(action_required_items, status_label):
    ssid_channel_texts = []

    for item in action_required_items:
        if item.get("status_label", "") != status_label:
            continue

        channel_text = item.get("channel", "")

        if channel_text == "":
            channel_text = "-"

        ssid_channel_texts.append(
            f"{item.get('ssid', '')}(channel={channel_text})",
        )

    return ssid_channel_texts


def get_trace_verdict(
    expected_5g_ssids,
    expected_2_4g_ssids,
    live_confirmed_5g_ssids,
    live_confirmed_2_4g_ssids,
    dead_confirmed_5g_ssids,
    dead_confirmed_2_4g_ssids,
    action_required_items,
    scan_ok,
    scan_message,
    error_message,
):
    missing_5g_ssids = get_action_required_ssids_by_status(
        action_required_items=action_required_items,
        status_label="MISSING_5G",
    )
    missing_2_4g_ssids = get_action_required_ssids_by_status(
        action_required_items=action_required_items,
        status_label="MISSING_2_4G",
    )
    not_confirmed_5g_ssids = get_action_required_ssid_channel_text_by_status(
        action_required_items=action_required_items,
        status_label="NOT_CONFIRMED_5G",
    )
    not_confirmed_2_4g_ssids = get_action_required_ssid_channel_text_by_status(
        action_required_items=action_required_items,
        status_label="NOT_CONFIRMED_2_4G",
    )
    not_confirmed_unknown_ssids = get_action_required_ssid_channel_text_by_status(
        action_required_items=action_required_items,
        status_label="NOT_CONFIRMED_UNKNOWN",
    )

    failure_reasons = []

    if error_message:
        failure_reasons.append(
            f"scan/read error: {error_message}",
        )

    if len(missing_5g_ssids) > 0:
        failure_reasons.append(
            f"missing expected 5G SSID(s): {', '.join(missing_5g_ssids)}",
        )

    if len(missing_2_4g_ssids) > 0:
        failure_reasons.append(
            f"missing expected 2.4G SSID(s): {', '.join(missing_2_4g_ssids)}",
        )

    if len(dead_confirmed_5g_ssids) > 0:
        failure_reasons.append(
            f"previously confirmed 5G SSID(s) not visible now: {', '.join(dead_confirmed_5g_ssids)}",
        )

    if len(dead_confirmed_2_4g_ssids) > 0:
        failure_reasons.append(
            f"previously confirmed 2.4G SSID(s) not visible now: {', '.join(dead_confirmed_2_4g_ssids)}",
        )

    if len(not_confirmed_5g_ssids) > 0:
        failure_reasons.append(
            f"unexpected 5G SSID(s): {', '.join(not_confirmed_5g_ssids)}",
        )

    if len(not_confirmed_2_4g_ssids) > 0:
        failure_reasons.append(
            f"unexpected 2.4G SSID(s): {', '.join(not_confirmed_2_4g_ssids)}",
        )

    if len(not_confirmed_unknown_ssids) > 0:
        failure_reasons.append(
            f"unexpected unknown-band SSID(s): {', '.join(not_confirmed_unknown_ssids)}",
        )

    if len(failure_reasons) > 0:
        failure_reasons.append(
            f"confirmed expected count: 5G={len(live_confirmed_5g_ssids)}/{len(expected_5g_ssids)}, 2.4G={len(live_confirmed_2_4g_ssids)}/{len(expected_2_4g_ssids)}",
        )

        if not scan_ok and scan_message:
            failure_reasons.append(
                f"scan warning: {scan_message}",
            )

    if len(failure_reasons) <= 0:
        return {
            "status_label": "PASSED",
            "failure_reasons": [],
        }

    return {
        "status_label": "FAILED",
        "failure_reasons": failure_reasons,
    }


def get_trace_verdict_text(trace_verdict):
    status_label = trace_verdict.get("status_label", "FAILED")

    if status_label == "PASSED":
        return "PASSED"

    failure_reasons = trace_verdict.get("failure_reasons", [])

    if len(failure_reasons) <= 0:
        return "FAILED: unknown reason"

    return f"FAILED: {' | '.join(failure_reasons)}"


def split_failure_reason(failure_reason):
    reason_label, separator, reason_detail = failure_reason.partition(": ")

    if separator == "":
        return failure_reason, ""

    return reason_label, reason_detail


def build_trace_verdict_section(trace_verdict):
    status_label = trace_verdict.get("status_label", "FAILED")

    if status_label == "PASSED":
        return build_rich_section(
            title="RESULT",
            renderables=[
                Text(
                    "Status : PASSED",
                    style=get_rich_style("green"),
                ),
                Text(
                    "All expected SSIDs are confirmed.",
                    style=get_rich_style("green"),
                ),
            ],
            border_style=get_rich_style("green"),
        )

    failure_reasons = trace_verdict.get("failure_reasons", [])
    renderables = [
        Text(
            "Status               : FAILED",
            style=get_rich_style("red"),
        ),
        Text(
            f"Failure Reason Count : {len(failure_reasons)}",
            style=get_rich_style("red"),
        ),
        Text(""),
        Text(
            "Failure Reasons",
            style=get_rich_style("red"),
        ),
    ]

    if len(failure_reasons) <= 0:
        renderables.append(
            Text("  - unknown reason", style=get_rich_style("red")),
        )
    else:
        for index, failure_reason in enumerate(failure_reasons, start=1):
            reason_label, reason_detail = split_failure_reason(
                failure_reason=failure_reason,
            )
            renderables.append(
                Text(
                    f"  {index:02d}. {reason_label}",
                    style=get_rich_style("red"),
                )
            )
            if reason_detail != "":
                renderables.append(
                    Text(
                        f"      {reason_detail}",
                        style=get_rich_style("red"),
                    )
                )

    return build_rich_section(
        title="RESULT",
        renderables=renderables,
        border_style=get_rich_style("red"),
    )


def print_trace_verdict(trace_verdict):
    get_rich_console().print(
        build_trace_verdict_section(
            trace_verdict=trace_verdict,
        )
    )


def print_confirmed_ssid_transition_list(
    title,
    status_label,
    live_ssids,
    dead_ssids,
):
    print("")
    print(get_green_text(title))

    rows = []

    for ssid in live_ssids:
        rows.append(
            {
                "ssid": ssid,
                "status_label": status_label,
                "color_name": "green",
            }
        )

    for ssid in dead_ssids:
        rows.append(
            {
                "ssid": ssid,
                "status_label": status_label,
                "color_name": "gray",
            }
        )

    rows = sorted(
        rows,
        key=lambda row: get_sort_key(
            value=row["ssid"],
        ),
    )

    if len(rows) <= 0:
        print("  -")
        return

    for index, row in enumerate(rows, start=1):
        line = f"  {index:02d}. {row['status_label']:<22} {row['ssid']}"
        print(get_colored_text(line, row["color_name"]))


def print_grouped_wifi_entry_list(title, status_label, wifi_entries, color_name):
    grouped_wifi_entries = get_grouped_wifi_entries_by_ssid_and_band(
        wifi_entries=wifi_entries,
    )

    print("")

    if color_name == "green":
        print(get_green_text(title))
    elif color_name == "gray":
        print(get_gray_text(title))
    elif color_name == "red":
        print(get_red_text(title))
    else:
        print(title)

    if len(grouped_wifi_entries) <= 0:
        print("  -")
        return

    for index, wifi_entry in enumerate(grouped_wifi_entries, start=1):
        channels_text = ", ".join(
            str(channel)
            for channel in wifi_entry.get("channels", [])
        )

        if channels_text == "":
            channels_text = "-"

        line = (
            f"  {index:02d}. "
            f"{status_label:<22} "
            f"{wifi_entry.get('ssid', ''):<32} "
            f"band={wifi_entry.get('band', ''):<7} "
            f"channels={channels_text:<12} "
            f"bssid_count={wifi_entry.get('bssid_count', 0)}"
        )

        if color_name == "green":
            print(get_green_text(line))
        elif color_name == "gray":
            print(get_gray_text(line))
        elif color_name == "red":
            print(get_red_text(line))
        else:
            print(line)


def print_action_required_statistics(
    action_required_items,
    live_confirmed_5g_count,
    live_confirmed_2_4g_count,
    dead_confirmed_5g_count,
    dead_confirmed_2_4g_count,
    missing_5g_count,
    missing_2_4g_count,
    not_confirmed_5g_count,
    not_confirmed_2_4g_count,
    not_confirmed_unknown_count,
    scan_ok,
    scan_message,
):
    get_rich_console().print(
        build_action_required_statistics_section(
            action_required_items=action_required_items,
            live_confirmed_5g_count=live_confirmed_5g_count,
            live_confirmed_2_4g_count=live_confirmed_2_4g_count,
            dead_confirmed_5g_count=dead_confirmed_5g_count,
            dead_confirmed_2_4g_count=dead_confirmed_2_4g_count,
            missing_5g_count=missing_5g_count,
            missing_2_4g_count=missing_2_4g_count,
            not_confirmed_5g_count=not_confirmed_5g_count,
            not_confirmed_2_4g_count=not_confirmed_2_4g_count,
            not_confirmed_unknown_count=not_confirmed_unknown_count,
            scan_ok=scan_ok,
            scan_message=scan_message,
        )
    )


def build_action_required_statistics_section(
    action_required_items,
    live_confirmed_5g_count,
    live_confirmed_2_4g_count,
    dead_confirmed_5g_count,
    dead_confirmed_2_4g_count,
    missing_5g_count,
    missing_2_4g_count,
    not_confirmed_5g_count,
    not_confirmed_2_4g_count,
    not_confirmed_unknown_count,
    scan_ok,
    scan_message,
):
    return build_rich_section(
        title="STATISTICS",
        renderables=[
            Text(f"Confirmed Count               : {live_confirmed_5g_count + live_confirmed_2_4g_count}"),
            Text(f"  - Confirmed 5G Count        : {live_confirmed_5g_count}"),
            Text(f"  - Confirmed 2.4G Count      : {live_confirmed_2_4g_count}"),
            Text(f"Dead Confirmed Count          : {dead_confirmed_5g_count + dead_confirmed_2_4g_count}"),
            Text(f"  - Dead Confirmed 5G Count   : {dead_confirmed_5g_count}"),
            Text(f"  - Dead Confirmed 2.4G Count : {dead_confirmed_2_4g_count}"),
            Text(f"Action Required Count         : {len(action_required_items)}"),
            Text(f"  - Missing 5G Count          : {missing_5g_count}"),
            Text(f"  - Missing 2.4G Count        : {missing_2_4g_count}"),
            Text(f"  - Not Confirmed 5G Count    : {not_confirmed_5g_count}"),
            Text(f"  - Not Confirmed 2.4G Count  : {not_confirmed_2_4g_count}"),
            Text(f"  - Not Confirmed Unknown     : {not_confirmed_unknown_count}"),
            Text(f"Scan Status                   : {'OK' if scan_ok else 'WARN'}"),
            Text(f"Scan Message                  : {scan_message}"),
            Text(f"Sort Mode                     : {'ASC' if SORT_OUTPUT_ASCENDING else 'RAW'}"),
            Text("Detected SSID Sort Mode       : status"),
            Text("Band Rule                     : 2.4G=Channel 1~14, 5G=Channel >=32"),
        ],
        border_style="white",
    )


def is_action_required_status_label(status_label):
    return "MISSING" in status_label or "NOT_CONFIRMED" in status_label


def get_detected_ssid_display_status_label(item, planned_ssid_set):
    status_label = item["status_label"]
    comparable_ssid = normalize_ssid_for_compare(
        ssid=item.get("ssid", ""),
    )

    if is_action_required_status_label(status_label) and comparable_ssid in planned_ssid_set:
        return f"PLANNED_{status_label}"

    return status_label


def get_detected_ssid_status_color_name(item, planned_ssid_set):
    status_label = item["status_label"]
    comparable_ssid = normalize_ssid_for_compare(
        ssid=item.get("ssid", ""),
    )

    if is_action_required_status_label(status_label) and comparable_ssid in planned_ssid_set:
        return "orange"
    if "MISSING" in status_label or "NOT_CONFIRMED" in status_label:
        return "red"
    if "DEAD" in status_label:
        return "gray"
    if "CONFIRMED" in status_label:
        return "green"
    if status_label == "IGNORED":
        return "green"

    return ""


def get_detected_ssid_status_sort_rank(item, planned_ssid_set):
    status_label = get_detected_ssid_display_status_label(
        item=item,
        planned_ssid_set=planned_ssid_set,
    )
    status_sort_rank_prefixes = [
        "MISSING_",
        "NOT_CONFIRMED_",
        "PLANNED_MISSING_",
        "PLANNED_NOT_CONFIRMED_",
        "DEAD_CONFIRMED_",
        "DEAD_DETECTED",
        "CONFIRMED_",
        "IGNORED",
    ]

    for index, status_prefix in enumerate(status_sort_rank_prefixes):
        if status_label.startswith(status_prefix):
            return index

    return len(status_sort_rank_prefixes)


def build_detected_ssid_section(
    live_confirmed_5g_ssids,
    live_confirmed_2_4g_ssids,
    dead_confirmed_5g_ssids,
    dead_confirmed_2_4g_ssids,
    dead_detected_wifi_entries,
    action_required_items,
    ignored_detected_wifi_entries,
    planned_ssids,
):
    rows = []
    planned_ssid_set = {
        normalize_ssid_for_compare(
            ssid=ssid,
        )
        for ssid in planned_ssids
    }

    for wifi_entry in live_confirmed_5g_ssids:
        channels_text = ", ".join(
            str(channel)
            for channel in wifi_entry.get("channels", [])
        )

        rows.append(
            {
                "status_label": "CONFIRMED_5G",
                "ssid": wifi_entry.get("ssid", ""),
                "band": "5G",
                "channel": channels_text,
                "reason": f"bssid_count={wifi_entry.get('bssid_count', 0)}",
            }
        )

    for wifi_entry in live_confirmed_2_4g_ssids:
        channels_text = ", ".join(
            str(channel)
            for channel in wifi_entry.get("channels", [])
        )

        rows.append(
            {
                "status_label": "CONFIRMED_2_4G",
                "ssid": wifi_entry.get("ssid", ""),
                "band": "2_4G",
                "channel": channels_text,
                "reason": f"bssid_count={wifi_entry.get('bssid_count', 0)}",
            }
        )

    for ssid in dead_confirmed_5g_ssids:
        rows.append(
            {
                "status_label": "DEAD_CONFIRMED_5G",
                "ssid": ssid,
                "band": "5G",
                "channel": "",
                "reason": "Expected 5GHz SSID was detected before but not now",
            }
        )

    for ssid in dead_confirmed_2_4g_ssids:
        rows.append(
            {
                "status_label": "DEAD_CONFIRMED_2_4G",
                "ssid": ssid,
                "band": "2_4G",
                "channel": "",
                "reason": "Expected 2.4GHz SSID was detected before but not now",
            }
        )

    rows.extend(
        action_required_items,
    )

    for wifi_entry in dead_detected_wifi_entries:
        channels_text = ", ".join(
            str(channel)
            for channel in wifi_entry.get("channels", [])
        )

        rows.append(
            {
                "status_label": "DEAD_DETECTED",
                "ssid": wifi_entry.get("ssid", ""),
                "band": wifi_entry.get("band", ""),
                "channel": channels_text,
                "reason": f"Previously detected, not present now; bssid_count={wifi_entry.get('bssid_count', 0)}",
            }
        )

    if SHOW_IGNORED_SSIDS:
        for wifi_entry in get_grouped_wifi_entries_by_ssid_and_band(
            wifi_entries=ignored_detected_wifi_entries,
        ):
            channels_text = ", ".join(
                str(channel)
                for channel in wifi_entry.get("channels", [])
            )

            rows.append(
                {
                    "status_label": "IGNORED",
                    "ssid": wifi_entry.get("ssid", ""),
                    "band": wifi_entry.get("band", ""),
                    "channel": channels_text,
                    "reason": f"bssid_count={wifi_entry.get('bssid_count', 0)}",
                }
            )

    sort_key_fields = [
        lambda row: get_sort_key(
            value=row["ssid"],
        ),
        lambda row: get_sort_key(
            value=row["status_label"],
        ),
        lambda row: get_sort_key(
            value=row.get("channel", ""),
        ),
    ]

    sort_key_fields.insert(
        0,
        lambda row: get_detected_ssid_status_sort_rank(
            item=row,
            planned_ssid_set=planned_ssid_set,
        ),
    )

    rows = sorted(
        rows,
        key=lambda row: tuple(
            sort_key_field(row)
            for sort_key_field in sort_key_fields
        ),
    )


    if len(rows) <= 0:
        return build_rich_section(
            title="DETECTED SSID",
            renderables=[],
            border_style="cyan",
        )

    renderables = []

    for index, item in enumerate(rows, start=1):
        channel_text = str(item.get("channel", ""))
        reason_text = item.get("reason", "")
        status_label = get_detected_ssid_display_status_label(
            item=item,
            planned_ssid_set=planned_ssid_set,
        )

        if channel_text == "":
            channel_text = "-"

        if reason_text != "":
            reason_text = f" # {reason_text}"

        line = (
            f"  {index:02d}. "
            f"{status_label:<30} "
            f"{item['ssid']:<32} "
            f"band={item.get('band', ''):<7} "
            f"channel={channel_text:<4}"
            f"{reason_text}"
        )

        renderables.append(
            Text(
                line,
                style=get_rich_style(
                    get_detected_ssid_status_color_name(
                        item=item,
                        planned_ssid_set=planned_ssid_set,
                    )
                ),
            )
        )

    return build_rich_section(
        title="DETECTED SSID",
        renderables=renderables,
        border_style="cyan",
    )


def print_detected_ssid_list(
    live_confirmed_5g_ssids,
    live_confirmed_2_4g_ssids,
    dead_confirmed_5g_ssids,
    dead_confirmed_2_4g_ssids,
    dead_detected_wifi_entries,
    action_required_items,
    ignored_detected_wifi_entries,
    planned_ssids,
):
    get_rich_console().print(
        build_detected_ssid_section(
            live_confirmed_5g_ssids=live_confirmed_5g_ssids,
            live_confirmed_2_4g_ssids=live_confirmed_2_4g_ssids,
            dead_confirmed_5g_ssids=dead_confirmed_5g_ssids,
            dead_confirmed_2_4g_ssids=dead_confirmed_2_4g_ssids,
            dead_detected_wifi_entries=dead_detected_wifi_entries,
            action_required_items=action_required_items,
            ignored_detected_wifi_entries=ignored_detected_wifi_entries,
            planned_ssids=planned_ssids,
        )
    )


def build_result_screen(
    expected_5g_ssids,
    expected_2_4g_ssids,
    ignored_ssids,
    planned_ssids,
    detected_wifi_entries,
    scan_ok,
    scan_message,
    error_message,
):
    (
        live_confirmed_5g_ssids,
        live_confirmed_2_4g_ssids,
        dead_confirmed_5g_ssids,
        dead_confirmed_2_4g_ssids,
        dead_detected_wifi_entries,
        action_required_items,
        ignored_detected_wifi_entries,
    ) = get_check_result(
        expected_5g_ssids=expected_5g_ssids,
        expected_2_4g_ssids=expected_2_4g_ssids,
        ignored_ssids=ignored_ssids,
        detected_wifi_entries=detected_wifi_entries,
    )

    missing_5g_count = 0
    missing_2_4g_count = 0
    not_confirmed_5g_count = 0
    not_confirmed_2_4g_count = 0
    not_confirmed_unknown_count = 0

    for item in action_required_items:
        if item["status_label"] == "MISSING_5G":
            missing_5g_count += 1
        elif item["status_label"] == "MISSING_2_4G":
            missing_2_4g_count += 1
        elif item["status_label"] == "NOT_CONFIRMED_5G":
            not_confirmed_5g_count += 1
        elif item["status_label"] == "NOT_CONFIRMED_2_4G":
            not_confirmed_2_4g_count += 1
        elif item["status_label"] == "NOT_CONFIRMED_UNKNOWN":
            not_confirmed_unknown_count += 1

    checked_at = time.strftime(
        "%Y-%m-%d %H:%M:%S",
    )

    trace_verdict = get_trace_verdict(
        expected_5g_ssids=expected_5g_ssids,
        expected_2_4g_ssids=expected_2_4g_ssids,
        live_confirmed_5g_ssids=live_confirmed_5g_ssids,
        live_confirmed_2_4g_ssids=live_confirmed_2_4g_ssids,
        dead_confirmed_5g_ssids=dead_confirmed_5g_ssids,
        dead_confirmed_2_4g_ssids=dead_confirmed_2_4g_ssids,
        action_required_items=action_required_items,
        scan_ok=scan_ok,
        scan_message=scan_message,
        error_message=error_message,
    )

    screen_renderables = [
        build_trace_verdict_section(
            trace_verdict=trace_verdict,
        ),
        Text(f"Checked At                    : {checked_at}"),
    ]

    if error_message:
        screen_renderables.append(
            Text(
                f"Error Message                 : {error_message}",
                style=get_rich_style("red"),
            )
        )

    if SHOW_ALL_DETECTED_WIFI_ENTRIES:
        screen_renderables.append(
            build_detected_ssid_section(
                live_confirmed_5g_ssids=live_confirmed_5g_ssids,
                live_confirmed_2_4g_ssids=live_confirmed_2_4g_ssids,
                dead_confirmed_5g_ssids=dead_confirmed_5g_ssids,
                dead_confirmed_2_4g_ssids=dead_confirmed_2_4g_ssids,
                dead_detected_wifi_entries=dead_detected_wifi_entries,
                action_required_items=action_required_items,
                ignored_detected_wifi_entries=ignored_detected_wifi_entries,
                planned_ssids=planned_ssids,
            )
        )

    screen_renderables.append(
        build_action_required_statistics_section(
            action_required_items=action_required_items,
            live_confirmed_5g_count=len(live_confirmed_5g_ssids),
            live_confirmed_2_4g_count=len(live_confirmed_2_4g_ssids),
            dead_confirmed_5g_count=len(dead_confirmed_5g_ssids),
            dead_confirmed_2_4g_count=len(dead_confirmed_2_4g_ssids),
            missing_5g_count=missing_5g_count,
            missing_2_4g_count=missing_2_4g_count,
            not_confirmed_5g_count=not_confirmed_5g_count,
            not_confirmed_2_4g_count=not_confirmed_2_4g_count,
            not_confirmed_unknown_count=not_confirmed_unknown_count,
            scan_ok=scan_ok,
            scan_message=scan_message,
        )
    )

    return Group(
        *screen_renderables,
    )


def print_result(
    expected_5g_ssids,
    expected_2_4g_ssids,
    ignored_ssids,
    planned_ssids,
    detected_wifi_entries,
    scan_ok,
    scan_message,
    error_message,
):
    get_rich_console().print(
        build_result_screen(
            expected_5g_ssids=expected_5g_ssids,
            expected_2_4g_ssids=expected_2_4g_ssids,
            ignored_ssids=ignored_ssids,
            planned_ssids=planned_ssids,
            detected_wifi_entries=detected_wifi_entries,
            scan_ok=scan_ok,
            scan_message=scan_message,
            error_message=error_message,
        )
    )


def ensure_wifi_expected_ssids_watched():
    ensure_ansi_color_enabled()

    expected_5g_ssids = get_unique_expected_5g_ssids()
    expected_2_4g_ssids = get_unique_expected_2_4g_ssids()
    ignored_ssids = get_unique_ignored_ssids()
    planned_ssids = get_unique_planned_ssids()

    if len(expected_5g_ssids) <= 0 and len(expected_2_4g_ssids) <= 0:
        print("No expected SSID defined")
        sys.exit(1)

    console = get_rich_console()

    with Live(
        Text("Starting Wi-Fi SSID tracer..."),
        console=console,
        refresh_per_second=4,
        screen=False,
        auto_refresh=False,
    ) as live:
        while True:
            loop_started_at = time.time()

            detected_wifi_entries, scan_ok, scan_message, error_message = get_detected_wifi_entries_with_retry()

            live.update(
                build_result_screen(
                    expected_5g_ssids=expected_5g_ssids,
                    expected_2_4g_ssids=expected_2_4g_ssids,
                    ignored_ssids=ignored_ssids,
                    planned_ssids=planned_ssids,
                    detected_wifi_entries=detected_wifi_entries,
                    scan_ok=scan_ok,
                    scan_message=scan_message,
                    error_message=error_message,
                ),
                refresh=True,
            )

            elapsed_sec = time.time() - loop_started_at
            sleep_sec = max(
                0.0,
                WATCH_INTERVAL_SEC - elapsed_sec,
            )

            time.sleep(
                sleep_sec,
            )


def main():
    ensure_wifi_expected_ssids_watched()


if __name__ == "__main__":
    main()
