import time

from rich.console import Group
from rich.text import Text

from ssid_analyzer import get_check_result, get_trace_verdict, get_trace_verdict_text
from ssid_config import SHOW_ALL_DETECTED_WIFI_ENTRIES
from ssid_logger import maybe_write_log
from ssid_renderer_base import (
    get_colored_text,
    get_gray_text,
    get_green_text,
    get_red_text,
    get_rich_console,
    get_rich_style,
    build_rich_section,
    print_rich_section,
)
from ssid_renderer_detected import build_detected_ssid_section, print_detected_ssid_list
from ssid_renderer_result import build_trace_verdict_section, print_trace_verdict
from ssid_utils import get_grouped_wifi_entries_by_ssid_and_band, get_sort_key


DISPLAY_SECTIONS = ("result", "detected", "statistics", "config", "all")


def print_confirmed_ssid_transition_list(title, status_label, live_ssids, dead_ssids):
    print("")
    print(get_green_text(title))

    rows = []
    for ssid in live_ssids:
        rows.append({"ssid": ssid, "status_label": status_label, "color_name": "green"})
    for ssid in dead_ssids:
        rows.append({"ssid": ssid, "status_label": status_label, "color_name": "gray"})

    rows = sorted(rows, key=lambda row: get_sort_key(value=row["ssid"]))

    if len(rows) <= 0:
        print("  -")
        return

    for index, row in enumerate(rows, start=1):
        line = f"  {index:02d}. {row['status_label']:<22} {row['ssid']}"
        print(get_colored_text(line, row["color_name"]))


def print_grouped_wifi_entry_list(title, status_label, wifi_entries, color_name):
    grouped_wifi_entries = get_grouped_wifi_entries_by_ssid_and_band(wifi_entries=wifi_entries)

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
        channels_text = ", ".join(str(ch) for ch in wifi_entry.get("channels", [])) or "-"
        line = (
            f"  {index:02d}. "
            f"{status_label:<22} "
            f"{wifi_entry.get('ssid', ''):<32} "
            f"band={wifi_entry.get('band', ''):<7} "
            f"channels={channels_text:<12} "
            f"bssid_count={wifi_entry.get('bssid_count', 0)}"
        )
        print(get_colored_text(line, color_name))


def build_action_required_statistics_section(
    action_required_items,
    detected_wifi_entries,
    live_confirmed_5g_count,
    live_confirmed_2_4g_count,
    dead_confirmed_5g_count,
    dead_confirmed_2_4g_count,
    scan_ok,
    scan_message,
):
    confirmed_count = live_confirmed_5g_count + live_confirmed_2_4g_count
    dead_confirmed_count = dead_confirmed_5g_count + dead_confirmed_2_4g_count
    return build_rich_section(
        title="STATISTICS",
        renderables=[
            Text(f"Detected        : {len(detected_wifi_entries)}"),
            Text(f"Confirmed       : {confirmed_count}"),
            Text(f"Dead Confirmed  : {dead_confirmed_count}"),
            Text(f"Action Required : {len(action_required_items)}"),
            Text(f"Scan Status     : {'OK' if scan_ok else 'WARN'}"),
            Text(f"Scan Message    : {scan_message}"),
        ],
        border_style="white",
    )


def build_config_section(config_name, expected_5g_ssids, expected_2_4g_ssids, ignored_ssids, planned_ssids):
    expected_ssids = list(expected_5g_ssids) + list(expected_2_4g_ssids)
    renderables = [
        Text(f"Selected Config : {config_name}"),
        Text(""),
        Text(f"Expected({len(expected_ssids)})"),
    ]

    renderables.extend(
        Text(f"  {index:02d}. {ssid}")
        for index, ssid in enumerate(expected_ssids, start=1)
    )
    renderables.append(Text(""))
    renderables.append(Text(f"Planned({len(planned_ssids)})"))
    renderables.extend(
        Text(f"  {index:02d}. {ssid}")
        for index, ssid in enumerate(planned_ssids, start=1)
    )
    renderables.append(Text(""))
    renderables.append(Text(f"Ignored({len(ignored_ssids)})"))
    renderables.extend(
        Text(f"  {index:02d}. {ssid}")
        for index, ssid in enumerate(ignored_ssids, start=1)
    )

    return build_rich_section(
        title="CONFIG",
        renderables=renderables,
        border_style="white",
    )


def build_result_screen(
    config_name,
    expected_5g_ssids,
    expected_2_4g_ssids,
    ignored_ssids,
    planned_ssids,
    detected_wifi_entries,
    scan_ok,
    scan_message,
    error_message,
    section_name="all",
):
    if section_name not in DISPLAY_SECTIONS:
        section_name = "all"

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

    checked_at = time.strftime("%Y-%m-%d %H:%M:%S")

    if config_name == "NOT SET":
        trace_verdict = {"status_label": "NOT_TESTED", "failure_reasons": []}
    else:
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
        maybe_write_log(get_trace_verdict_text(trace_verdict))

    result_renderables = [
        build_trace_verdict_section(trace_verdict=trace_verdict),
        Text(f"Checked At                    : {checked_at}"),
    ]

    if error_message:
        result_renderables.append(
            Text(f"Error Message                 : {error_message}", style=get_rich_style("red"))
        )

    detected_section = build_detected_ssid_section(
        live_confirmed_5g_ssids=live_confirmed_5g_ssids,
        live_confirmed_2_4g_ssids=live_confirmed_2_4g_ssids,
        dead_confirmed_5g_ssids=dead_confirmed_5g_ssids,
        dead_confirmed_2_4g_ssids=dead_confirmed_2_4g_ssids,
        dead_detected_wifi_entries=dead_detected_wifi_entries,
        action_required_items=action_required_items,
        ignored_detected_wifi_entries=ignored_detected_wifi_entries,
        planned_ssids=planned_ssids,
    )

    statistics_section = build_action_required_statistics_section(
        action_required_items=action_required_items,
        detected_wifi_entries=detected_wifi_entries,
        live_confirmed_5g_count=len(live_confirmed_5g_ssids),
        live_confirmed_2_4g_count=len(live_confirmed_2_4g_ssids),
        dead_confirmed_5g_count=len(dead_confirmed_5g_ssids),
        dead_confirmed_2_4g_count=len(dead_confirmed_2_4g_ssids),
        scan_ok=scan_ok,
        scan_message=scan_message,
    )

    config_section = build_config_section(
        config_name=config_name,
        expected_5g_ssids=expected_5g_ssids,
        expected_2_4g_ssids=expected_2_4g_ssids,
        ignored_ssids=ignored_ssids,
        planned_ssids=planned_ssids,
    )

    if section_name == "result":
        return Group(*result_renderables)
    if section_name == "detected":
        return Group(detected_section)
    if section_name == "statistics":
        return Group(statistics_section)
    if section_name == "config":
        return Group(config_section)

    screen_renderables = result_renderables

    if SHOW_ALL_DETECTED_WIFI_ENTRIES:
        screen_renderables.append(detected_section)

    screen_renderables.extend(
        [
            statistics_section,
            config_section,
        ]
    )

    return Group(*screen_renderables)


def print_result(
    config_name,
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
            config_name=config_name,
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
