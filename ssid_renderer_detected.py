from rich.text import Text

from ssid_config import SHOW_IGNORED_SSIDS
from ssid_renderer_base import build_rich_section, get_rich_console, get_rich_style
from ssid_utils import get_grouped_wifi_entries_by_ssid_and_band, get_sort_key, normalize_ssid_for_compare


def is_action_required_status_label(status_label):
    return "MISSING" in status_label or "NOT_CONFIRMED" in status_label


def get_detected_ssid_display_status_label(item, planned_ssid_set):
    status_label = item["status_label"]
    comparable_ssid = normalize_ssid_for_compare(ssid=item.get("ssid", ""))
    if is_action_required_status_label(status_label) and comparable_ssid in planned_ssid_set:
        return f"PLANNED_{status_label}"
    return status_label


def get_compact_detected_ssid_status_label(status_label):
    if status_label.startswith("PLANNED_"):
        return "PLANNED"
    if "MISSING" in status_label:
        return "MISSING"
    if "NOT_CONFIRMED" in status_label:
        return "UNEXPECTED"
    if "DEAD" in status_label:
        return "DEAD"
    if "CONFIRMED" in status_label:
        return "CONFIRMED"
    if status_label == "IGNORED":
        return "IGNORED"
    return status_label


def get_detected_ssid_status_color_name(item, planned_ssid_set):
    status_label = item["status_label"]
    comparable_ssid = normalize_ssid_for_compare(ssid=item.get("ssid", ""))
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
    status_label = get_detected_ssid_display_status_label(item=item, planned_ssid_set=planned_ssid_set)
    prefixes = [
        "MISSING_",
        "NOT_CONFIRMED_",
        "PLANNED_MISSING_",
        "PLANNED_NOT_CONFIRMED_",
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
    return f"DETECTED SSIDS({detected_ssid_count})"


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

    for ssid in dead_confirmed_5g_ssids:
        rows.append({"status_label": "DEAD_CONFIRMED_5G", "ssid": ssid, "band": "5G", "channel": "", "reason": "Expected 5GHz SSID was detected before but not now"})

    for ssid in dead_confirmed_2_4g_ssids:
        rows.append({"status_label": "DEAD_CONFIRMED_2_4G", "ssid": ssid, "band": "2_4G", "channel": "", "reason": "Expected 2.4GHz SSID was detected before but not now"})

    rows.extend(action_required_items)

    for wifi_entry in dead_detected_wifi_entries:
        channels_text = ", ".join(str(ch) for ch in wifi_entry.get("channels", []))
        rows.append({"status_label": "DEAD_DETECTED", "ssid": wifi_entry.get("ssid", ""), "band": wifi_entry.get("band", ""), "channel": channels_text, "reason": f"Previously detected, not present now; bssid_count={wifi_entry.get('bssid_count', 0)}"})

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

    if len(rows) <= 0:
        return build_rich_section(title=title, renderables=[], border_style="cyan")

    renderables = []
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

    return build_rich_section(title=title, renderables=renderables, border_style="white")


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
