from pathlib import Path

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

PLANNED_SSIDS_RAW = [
    "Linksys00711",
    "Cuby-A254-5G",
    "Cuby-A254",
    "_LinksysSetup99A",
    "R15-FEFA",
]

WATCH_INTERVAL_SEC = 0.25
SCAN_SETTLE_SEC = 0.15
NETSH_RETRY_COUNT = 2
NETSH_RETRY_SETTLE_SEC = 0.05

SKIP_TBD = True
CASE_SENSITIVE = True
SHOW_ALL_DETECTED_WIFI_ENTRIES = True
SHOW_IGNORED_SSIDS = True
SORT_OUTPUT_ASCENDING = True
ENABLE_ANSI_COLOR = True
LOG_ENABLE = True
LOG_DIR = Path(__file__).parent / "logs"
LOG_INTERVAL_SEC = 60

ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_GRAY = "\033[90m"
ANSI_ORANGE = "\033[38;5;208m"
ANSI_RESET = "\033[0m"
