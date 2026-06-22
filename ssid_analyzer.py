from ssid_utils import (
    get_grouped_wifi_entries_by_ssid_and_band,
    get_sorted_ssids,
    get_sorted_wifi_entries,
    normalize_ssid_for_compare,
)

EVER_LIVE_CONFIRMED_SSID_BAND_SET: set = set()
EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY: dict = {}


def get_detected_ssid_band_set(detected_wifi_entries):
    detected_ssid_band_set = set()
    for wifi_entry in detected_wifi_entries:
        comparable_ssid = normalize_ssid_for_compare(ssid=wifi_entry.get("ssid", ""))
        band = wifi_entry.get("band", "UNKNOWN")
        detected_ssid_band_set.add((comparable_ssid, band))
    return detected_ssid_band_set


def get_wifi_group_key(ssid, band):
    return (normalize_ssid_for_compare(ssid=ssid), band)


def get_expected_ssid_band_set(expected_5g_ssids, expected_2_4g_ssids):
    expected_ssid_band_set = set()
    for ssid in expected_5g_ssids:
        expected_ssid_band_set.add((normalize_ssid_for_compare(ssid=ssid), "5G"))
    for ssid in expected_2_4g_ssids:
        expected_ssid_band_set.add((normalize_ssid_for_compare(ssid=ssid), "2_4G"))
    return expected_ssid_band_set


def get_check_result(expected_5g_ssids, expected_2_4g_ssids, ignored_ssids, detected_wifi_entries):
    global EVER_LIVE_CONFIRMED_SSID_BAND_SET
    global EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY

    expected_ssid_band_set = get_expected_ssid_band_set(
        expected_5g_ssids=expected_5g_ssids,
        expected_2_4g_ssids=expected_2_4g_ssids,
    )

    ignored_set = {normalize_ssid_for_compare(ssid=ssid) for ssid in ignored_ssids}

    detected_ssid_band_set = get_detected_ssid_band_set(detected_wifi_entries=detected_wifi_entries)
    grouped_detected_wifi_entries = get_grouped_wifi_entries_by_ssid_and_band(wifi_entries=detected_wifi_entries)
    current_detected_wifi_group_keys = set()

    for grouped_wifi_entry in grouped_detected_wifi_entries:
        group_key = get_wifi_group_key(
            ssid=grouped_wifi_entry.get("ssid", ""),
            band=grouped_wifi_entry.get("band", "UNKNOWN"),
        )
        current_detected_wifi_group_keys.add(group_key)
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

    current_live_confirmed_set = expected_ssid_band_set.intersection(detected_ssid_band_set)
    EVER_LIVE_CONFIRMED_SSID_BAND_SET.update(current_live_confirmed_set)

    for expected_ssid in expected_5g_ssids:
        comparable_expected_ssid = normalize_ssid_for_compare(ssid=expected_ssid)
        expected_key = (comparable_expected_ssid, "5G")

        if expected_key in detected_ssid_band_set:
            live_confirmed_5g_ssids.append(
                grouped_detected_wifi_entry_by_group_key.get(
                    expected_key,
                    {"ssid": expected_ssid, "band": "5G", "channels": [], "bssids": [], "bssid_count": 0},
                )
            )
        elif expected_key in EVER_LIVE_CONFIRMED_SSID_BAND_SET:
            dead_confirmed_5g_ssids.append(expected_ssid)
        else:
            missing_5g_ssids.append(expected_ssid)

    for expected_ssid in expected_2_4g_ssids:
        comparable_expected_ssid = normalize_ssid_for_compare(ssid=expected_ssid)
        expected_key = (comparable_expected_ssid, "2_4G")

        if expected_key in detected_ssid_band_set:
            live_confirmed_2_4g_ssids.append(
                grouped_detected_wifi_entry_by_group_key.get(
                    expected_key,
                    {"ssid": expected_ssid, "band": "2_4G", "channels": [], "bssids": [], "bssid_count": 0},
                )
            )
        elif expected_key in EVER_LIVE_CONFIRMED_SSID_BAND_SET:
            dead_confirmed_2_4g_ssids.append(expected_ssid)
        else:
            missing_2_4g_ssids.append(expected_ssid)

    ignored_detected_wifi_entries = []
    not_confirmed_wifi_entries = []
    seen_ignored_entry_keys = set()
    seen_not_confirmed_entry_keys = set()

    for wifi_entry in detected_wifi_entries:
        ssid = wifi_entry.get("ssid", "")
        channel = wifi_entry.get("channel", 0)
        band = wifi_entry.get("band", "UNKNOWN")
        bssid = wifi_entry.get("bssid", "")

        comparable_ssid = normalize_ssid_for_compare(ssid=ssid)
        wifi_entry_key = (comparable_ssid, band, channel, bssid)

        if comparable_ssid in ignored_set:
            if wifi_entry_key not in seen_ignored_entry_keys:
                ignored_detected_wifi_entries.append(wifi_entry)
                seen_ignored_entry_keys.add(wifi_entry_key)
            continue

        if (comparable_ssid, band) not in expected_ssid_band_set:
            if wifi_entry_key not in seen_not_confirmed_entry_keys:
                not_confirmed_wifi_entries.append(wifi_entry)
                seen_not_confirmed_entry_keys.add(wifi_entry_key)

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
        channels_text = ", ".join(str(channel) for channel in wifi_entry.get("channels", []))

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

    from ssid_utils import get_sort_key

    live_confirmed_5g_ssids = get_sorted_wifi_entries(wifi_entries=live_confirmed_5g_ssids)
    live_confirmed_2_4g_ssids = get_sorted_wifi_entries(wifi_entries=live_confirmed_2_4g_ssids)
    dead_confirmed_5g_ssids = get_sorted_ssids(ssids=dead_confirmed_5g_ssids)
    dead_confirmed_2_4g_ssids = get_sorted_ssids(ssids=dead_confirmed_2_4g_ssids)
    ignored_detected_wifi_entries = get_sorted_wifi_entries(wifi_entries=ignored_detected_wifi_entries)
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
            get_sort_key(value=item["ssid"]),
            get_sort_key(value=item["status_label"]),
            get_sort_key(value=item.get("channel", "")),
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
        ssid_channel_texts.append(f"{item.get('ssid', '')}(channel={channel_text})")
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
        action_required_items=action_required_items, status_label="MISSING_5G"
    )
    missing_2_4g_ssids = get_action_required_ssids_by_status(
        action_required_items=action_required_items, status_label="MISSING_2_4G"
    )
    not_confirmed_5g_ssids = get_action_required_ssid_channel_text_by_status(
        action_required_items=action_required_items, status_label="NOT_CONFIRMED_5G"
    )
    not_confirmed_2_4g_ssids = get_action_required_ssid_channel_text_by_status(
        action_required_items=action_required_items, status_label="NOT_CONFIRMED_2_4G"
    )
    not_confirmed_unknown_ssids = get_action_required_ssid_channel_text_by_status(
        action_required_items=action_required_items, status_label="NOT_CONFIRMED_UNKNOWN"
    )

    failure_reasons = []
    failure_ssids = []

    if error_message:
        failure_reasons.append(f"scan/read error: {error_message}")

    missing_ssids = missing_5g_ssids + missing_2_4g_ssids
    if len(missing_ssids) > 0:
        failure_reasons.append(f"missing expected SSID(s): {', '.join(missing_ssids)}")
        failure_ssids.extend(
            {"status_label": "MISSING", "ssid": ssid}
            for ssid in missing_ssids
        )

    dead_confirmed_ssids = list(dead_confirmed_5g_ssids) + list(dead_confirmed_2_4g_ssids)
    if len(dead_confirmed_ssids) > 0:
        failure_reasons.append(f"previously confirmed SSID(s) not visible now: {', '.join(dead_confirmed_ssids)}")
        failure_ssids.extend(
            {"status_label": "DEAD", "ssid": ssid}
            for ssid in dead_confirmed_ssids
        )

    not_confirmed_ssids = not_confirmed_5g_ssids + not_confirmed_2_4g_ssids
    if len(not_confirmed_ssids) > 0:
        failure_reasons.append(f"unexpected SSID(s): {', '.join(not_confirmed_ssids)}")
        failure_ssids.extend(
            {"status_label": "Unexpected", "ssid": ssid}
            for ssid in not_confirmed_ssids
        )

    if len(not_confirmed_unknown_ssids) > 0:
        failure_reasons.append(f"unexpected unknown-band SSID(s): {', '.join(not_confirmed_unknown_ssids)}")
        failure_ssids.extend(
            {"status_label": "Unexpected Unknown", "ssid": ssid}
            for ssid in not_confirmed_unknown_ssids
        )

    if len(failure_reasons) > 0:
        total_confirmed = len(live_confirmed_5g_ssids) + len(live_confirmed_2_4g_ssids)
        total_expected = len(expected_5g_ssids) + len(expected_2_4g_ssids)
        failure_reasons.append(f"confirmed expected count: {total_confirmed}/{total_expected}")

        if not scan_ok and scan_message:
            failure_reasons.append(f"scan warning: {scan_message}")

    if len(failure_reasons) <= 0:
        return {"status_label": "PASSED", "failure_reasons": [], "failure_ssids": []}

    return {
        "status_label": "FAILED",
        "failure_reasons": failure_reasons,
        "failure_ssids": failure_ssids,
    }


def get_trace_verdict_text(trace_verdict):
    status_label = trace_verdict.get("status_label", "FAILED")

    if status_label == "PASSED":
        return "PASSED"

    failure_reasons = trace_verdict.get("failure_reasons", [])

    if len(failure_reasons) <= 0:
        return "FAILED: unknown reason"

    return f"FAILED: {' | '.join(failure_reasons)}"
