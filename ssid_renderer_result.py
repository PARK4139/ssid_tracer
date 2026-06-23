from rich.console import Group
from rich.text import Text

from ssid_renderer_base import get_rich_console, get_rich_style
from ssid_utils import get_sort_key


def get_failure_ssid_renderables(failure_ssids):
    if len(failure_ssids) <= 0:
        return [Text("    01. [UNKNOWN] unknown reason", style=get_rich_style("white"))]

    status_label_order = []
    grouped_failure_ssids = {}
    for failure_ssid in failure_ssids:
        status_label = failure_ssid.get("status_label", "UNKNOWN")
        if status_label not in grouped_failure_ssids:
            grouped_failure_ssids[status_label] = []
            status_label_order.append(status_label)
        grouped_failure_ssids[status_label].append(failure_ssid)

    renderables = []
    index = 1
    for status_label in status_label_order:
        for failure_ssid in sorted(
            grouped_failure_ssids[status_label],
            key=lambda item: get_sort_key(value=item.get("ssid", "")),
        ):
            ssid = failure_ssid.get("ssid", "")
            renderables.append(Text(f"    {index:02d}. [{status_label}] {ssid}", style=get_rich_style("white")))
            index += 1
    return renderables


def build_trace_verdict_section(trace_verdict, config_name=None, checked_at=None, error_message=""):
    status_label = trace_verdict.get("status_label", "FAILED")
    renderables = [Text("# RESULT", style=get_rich_style("white"))]

    status_text = Text("Status               : ")
    if status_label == "PASSED":
        status_text.append("PASSED", style=get_rich_style("green"))
    elif status_label == "NOT_TESTED":
        status_text.append("NOT TESTED", style=get_rich_style("white"))
    else:
        status_text.append("FAILED", style=get_rich_style("red"))
    renderables.append(status_text)

    if config_name is not None:
        renderables.append(Text(f"Selected Config                : {config_name}", style=get_rich_style("white")))

    if checked_at is not None:
        renderables.append(Text(f"Checked At                    : {checked_at}", style=get_rich_style("white")))

    if error_message:
        renderables.append(Text(f"Error Message                 : {error_message}", style=get_rich_style("red")))

    if status_label == "PASSED":
        renderables.append(Text("All expected SSIDs are intended.", style=get_rich_style("white")))
    elif status_label == "FAILED":
        renderables.append(Text("Failure SSIDS", style=get_rich_style("white")))
        renderables.extend(get_failure_ssid_renderables(failure_ssids=trace_verdict.get("failure_ssids", [])))

    return Group(*renderables)


def build_not_tested_result_section():
    return build_trace_verdict_section(
        trace_verdict={"status_label": "NOT_TESTED"},
        config_name="NOT SET",
    )


def print_trace_verdict(trace_verdict):
    get_rich_console().print(build_trace_verdict_section(trace_verdict=trace_verdict))
