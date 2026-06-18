import ctypes
import re
import subprocess
import time
from ctypes import wintypes

from ssid_config import NETSH_RETRY_COUNT, NETSH_RETRY_SETTLE_SEC, SCAN_SETTLE_SEC
from ssid_utils import get_band_from_channel


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
        WlanFreeMemory.argtypes = [wintypes.LPVOID]
        WlanFreeMemory.restype = None

        WlanCloseHandle = wlanapi.WlanCloseHandle
        WlanCloseHandle.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
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
            interface_size = ctypes.sizeof(WLAN_INTERFACE_INFO)

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
                WlanFreeMemory(interface_list_pointer)
            WlanCloseHandle(client_handle, None)

    except Exception as exception:
        return False, f"WlanScan exception: {exception}"


def get_decoded_text(raw_bytes):
    for encoding in ["cp949", "utf-8", "utf-16"]:
        try:
            return raw_bytes.decode(encoding=encoding, errors="strict")
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode(encoding="cp949", errors="replace")


def get_netsh_output():
    completed_process = subprocess.run(
        ["netsh", "wlan", "show", "networks", "mode=bssid"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    stdout_text = get_decoded_text(raw_bytes=completed_process.stdout)
    stderr_text = get_decoded_text(raw_bytes=completed_process.stderr)
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
        band = get_band_from_channel(channel=channel)

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

        time.sleep(SCAN_SETTLE_SEC)

        detected_wifi_entries, error_message = get_detected_wifi_entries_once()

        if len(detected_wifi_entries) > 0:
            return detected_wifi_entries, scan_ok, scan_message, ""

        last_error_message = error_message

        time.sleep(NETSH_RETRY_SETTLE_SEC)

    return [], last_scan_ok, last_scan_message, last_error_message
