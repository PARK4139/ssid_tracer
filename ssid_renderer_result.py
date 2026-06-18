from rich.text import Text

from ssid_renderer_base import build_rich_section, get_rich_console, get_rich_style


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
                Text("Status : PASSED", style=get_rich_style("green")),
                Text("All expected SSIDs are confirmed.", style=get_rich_style("green")),
            ],
            border_style=get_rich_style("green"),
        )

    failure_reasons = trace_verdict.get("failure_reasons", [])
    renderables = [
        Text("Status               : FAILED", style=get_rich_style("red")),
        Text(f"Failure Reason Count : {len(failure_reasons)}", style=get_rich_style("red")),
        Text(""),
        Text("Failure Reasons", style=get_rich_style("red")),
    ]

    if len(failure_reasons) <= 0:
        renderables.append(Text("  - unknown reason", style=get_rich_style("red")))
    else:
        for index, failure_reason in enumerate(failure_reasons, start=1):
            reason_label, reason_detail = split_failure_reason(failure_reason=failure_reason)
            renderables.append(Text(f"  {index:02d}. {reason_label}", style=get_rich_style("red")))
            if reason_detail != "":
                for detail_item in reason_detail.split(", "):
                    renderables.append(Text(f"        - {detail_item}", style=get_rich_style("red")))

    return build_rich_section(
        title="RESULT",
        renderables=renderables,
        border_style=get_rich_style("red"),
    )


def print_trace_verdict(trace_verdict):
    get_rich_console().print(build_trace_verdict_section(trace_verdict=trace_verdict))
