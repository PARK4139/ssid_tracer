from ssid_config import (
    CASE_SENSITIVE,
    DEFAULT_SSID_CONFIG_NAME,
    EXPECTED_2_4G_SSIDS_RAW,
    EXPECTED_5G_SSIDS_RAW,
    IGNORED_SSIDS_RAW,
    PLANNED_SSIDS_RAW,
    SELECTED_SSID_CONFIG_PATH,
    SKIP_TBD,
    SORT_OUTPUT_ASCENDING,
    SSID_CONFIGS,
)


def normalize_ssid_for_compare(ssid):
    if CASE_SENSITIVE:
        return ssid
    return ssid.lower()


def get_sort_key(value):
    return str(value).casefold()


def get_wifi_entry_sort_key(wifi_entry):
    return (
        get_sort_key(value=wifi_entry.get("ssid", "")),
        get_sort_key(value=wifi_entry.get("band", "")),
        int(wifi_entry.get("channel", 0) or 0),
    )


def get_sorted_ssids(ssids):
    if not SORT_OUTPUT_ASCENDING:
        return list(ssids)
    return sorted(ssids, key=get_sort_key)


def get_sorted_wifi_entries(wifi_entries):
    if not SORT_OUTPUT_ASCENDING:
        return list(wifi_entries)
    return sorted(wifi_entries, key=get_wifi_entry_sort_key)


def get_unique_ssids(raw_ssids, skip_tbd):
    unique_ssids = []
    seen = set()

    for ssid in raw_ssids:
        normalized_ssid = ssid.strip()

        if normalized_ssid == "":
            continue

        if skip_tbd and normalized_ssid.upper() == "TBD":
            continue

        comparable_ssid = normalize_ssid_for_compare(ssid=normalized_ssid)

        if comparable_ssid in seen:
            continue

        seen.add(comparable_ssid)
        unique_ssids.append(normalized_ssid)

    return unique_ssids


def get_unique_expected_5g_ssids():
    return get_unique_ssids(raw_ssids=EXPECTED_5G_SSIDS_RAW, skip_tbd=SKIP_TBD)


def get_unique_expected_2_4g_ssids():
    return get_unique_ssids(raw_ssids=EXPECTED_2_4G_SSIDS_RAW, skip_tbd=SKIP_TBD)


def get_unique_ignored_ssids():
    return get_unique_ssids(raw_ssids=IGNORED_SSIDS_RAW, skip_tbd=True)


def get_unique_planned_ssids():
    return get_unique_ssids(raw_ssids=PLANNED_SSIDS_RAW, skip_tbd=True)


def get_available_ssid_config_names():
    return list(SSID_CONFIGS.keys())


def get_completed_ssid_config_name(ssid_config_name):
    if ssid_config_name in SSID_CONFIGS:
        return ssid_config_name
    return DEFAULT_SSID_CONFIG_NAME


def ensure_selected_ssid_config_name_written(ssid_config_name):
    completed_ssid_config_name = get_completed_ssid_config_name(ssid_config_name=ssid_config_name)
    SELECTED_SSID_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_selected_ssid_config_path = SELECTED_SSID_CONFIG_PATH.with_suffix(".tmp")
    temporary_selected_ssid_config_path.write_text(completed_ssid_config_name, encoding="utf-8")
    temporary_selected_ssid_config_path.replace(SELECTED_SSID_CONFIG_PATH)
    return completed_ssid_config_name


def get_selected_ssid_config_name():
    if not SELECTED_SSID_CONFIG_PATH.exists():
        return ensure_selected_ssid_config_name_written(ssid_config_name=DEFAULT_SSID_CONFIG_NAME)

    selected_ssid_config_name = SELECTED_SSID_CONFIG_PATH.read_text(encoding="utf-8").strip()
    if selected_ssid_config_name in SSID_CONFIGS:
        return selected_ssid_config_name

    return ensure_selected_ssid_config_name_written(ssid_config_name=DEFAULT_SSID_CONFIG_NAME)


def get_selected_ssid_config():
    return get_ssid_config_by_name(ssid_config_name=get_selected_ssid_config_name())


def get_ssid_config_by_name(ssid_config_name):
    return SSID_CONFIGS[get_completed_ssid_config_name(ssid_config_name=ssid_config_name)]


def get_unique_expected_5g_ssids_from_selected_config():
    selected_ssid_config = get_selected_ssid_config()
    return get_unique_ssids(raw_ssids=selected_ssid_config["expected_5g_ssids"], skip_tbd=SKIP_TBD)


def get_unique_expected_2_4g_ssids_from_selected_config():
    selected_ssid_config = get_selected_ssid_config()
    return get_unique_ssids(raw_ssids=selected_ssid_config["expected_2_4g_ssids"], skip_tbd=SKIP_TBD)


def get_unique_ignored_ssids_from_selected_config():
    selected_ssid_config = get_selected_ssid_config()
    return get_unique_ssids(raw_ssids=selected_ssid_config["ignored_ssids"], skip_tbd=True)


def get_unique_planned_ssids_from_selected_config():
    selected_ssid_config = get_selected_ssid_config()
    return get_unique_ssids(raw_ssids=selected_ssid_config["planned_ssids"], skip_tbd=True)


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

        comparable_ssid = normalize_ssid_for_compare(ssid=ssid)
        group_key = (comparable_ssid, band)

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
        channels = sorted(grouped_entry["channels"], key=lambda value: int(value))
        bssids = sorted(grouped_entry["bssids"], key=get_sort_key)

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
            get_sort_key(value=item.get("ssid", "")),
            get_sort_key(value=item.get("band", "")),
        ),
    )
