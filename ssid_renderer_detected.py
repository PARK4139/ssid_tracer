from rich.console import Group
from rich.text import Text

from ssid_config import SHOW_IGNORED_SSIDS
from ssid_renderer_base import get_rich_console, get_rich_style
from ssid_utils import get_grouped_wifi_entries_by_ssid_and_band, get_sort_key, normalize_ssid_for_compare


def is_action_required_status_label(status_label):
    return "MISSING" in status_label or "NOT_CONFIRMED" in status_label


def get_detected_ssid_display_status_label(item, planned_ssid_set):
    return item["status_label"]


def get_compact_detected_ssid_status_label(status_label):
    if "MISSING" in status_label:
        return "MISSING"
    if "NOT_CONFIRMED" in status_label:
        return "Unexpected"
    if "DEAD" in status_label:
        return "DEAD"
    if "CONFIRMED" in status_label:
        return "INTENDED"
    if status_label == "IGNORED":
        return "Ignored"
    return status_label


def get_detected_ssid_status_sort_rank(item, planned_ssid_set):
    status_label = get_detected_ssid_display_status_label(item=item, planned_ssid_set=planned_ssid_set)
    prefixes = [
        "MISSING_",
        "NOT_CONFIRMED_",
        "DEAD_CONFIRMED_",
        "DEAD_DETECTED",
        "CONFIRMED_",
        "IGNORED",
    ]
    for index, prefix in enumerate(prefixes):
        if status_label.startswith(prefix):
            return index
    return len(prefixes)


def get_detected_ssid_section_title(detected_ssid_count):
    return f"LIVE SSIDS({detected_ssid_count})"


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
    planned_ssid_set = {normalize_ssid_for_compare(ssid=ssid) for ssid in planned_ssids}

    for wifi_entry in live_confirmed_5g_ssids:
        channels_text = ", ".join(str(ch) for ch in wifi_entry.get("channels", []))
        rows.append({"status_label": "CONFIRMED_5G", "ssid": wifi_entry.get("ssid", ""), "band": "5G", "channel": channels_text, "reason": f"bssid_count={wifi_entry.get('bssid_count', 0)}"})

    for wifi_entry in live_confirmed_2_4g_ssids:
        channels_text = ", ".join(str(ch) for ch in wifi_entry.get("channels", []))
        rows.append({"status_label": "CONFIRMED_2_4G", "ssid": wifi_entry.get("ssid", ""), "band": "2_4G", "channel": channels_text, "reason": f"bssid_count={wifi_entry.get('bssid_count', 0)}"})

    rows.extend(
        item
        for item in action_required_items
        if "NOT_CONFIRMED" in item.get("status_label", "")
    )

    if SHOW_IGNORED_SSIDS:
        for wifi_entry in get_grouped_wifi_entries_by_ssid_and_band(wifi_entries=ignored_detected_wifi_entries):
            channels_text = ", ".join(str(ch) for ch in wifi_entry.get("channels", []))
            rows.append({"status_label": "IGNORED", "ssid": wifi_entry.get("ssid", ""), "band": wifi_entry.get("band", ""), "channel": channels_text, "reason": f"bssid_count={wifi_entry.get('bssid_count', 0)}"})

    sort_key_fields = [
        lambda row: get_detected_ssid_status_sort_rank(item=row, planned_ssid_set=planned_ssid_set),
        lambda row: get_sort_key(value=row["ssid"]),
        lambda row: get_sort_key(value=row["status_label"]),
        lambda row: get_sort_key(value=row.get("channel", "")),
    ]

    rows = sorted(rows, key=lambda row: tuple(f(row) for f in sort_key_fields))

    title = get_detected_ssid_section_title(detected_ssid_count=len(rows))
    renderables = [Text(f"# {title}")]

    for index, item in enumerate(rows, start=1):
        channel_text = str(item.get("channel", "")) or "-"
        status_label = get_compact_detected_ssid_status_label(
            status_label=get_detected_ssid_display_status_label(
                item=item,
                planned_ssid_set=planned_ssid_set,
            )
        )

        line = (
            f"  {index:02d}. "
            f"{item['ssid']} "
            f"{status_label} "
            f"band={item.get('band', '')} "
            f"ch={channel_text}"
        )

        renderables.append(Text(line, style=get_rich_style("white")))

    return Group(*renderables)


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
