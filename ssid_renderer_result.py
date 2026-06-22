from rich.text import Text

from ssid_renderer_base import build_rich_section, get_rich_console, get_rich_style


def get_failure_ssid_renderables(failure_ssids):
    if len(failure_ssids) <= 0:
        return [Text("  - [UNKNOWN] unknown reason", style=get_rich_style("white"))]

    renderables = []
    for failure_ssid in failure_ssids:
        status_label = failure_ssid.get("status_label", "UNKNOWN")
        ssid = failure_ssid.get("ssid", "")
        renderables.append(Text(f"  - [{status_label}] {ssid}", style=get_rich_style("white")))
    return renderables


def build_trace_verdict_section(trace_verdict):
    status_label = trace_verdict.get("status_label", "FAILED")

    if status_label == "NOT_TESTED":
        return build_rich_section(
            title="RESULT",
            renderables=[
                Text("Status               : NOT TESTED", style=get_rich_style("white")),
                Text("Config               : NOT SET", style=get_rich_style("white")),
            ],
            border_style=get_rich_style("white"),
        )

    if status_label == "PASSED":
        status_text = Text("Status : ")
        status_text.append("PASSED", style=get_rich_style("green"))
        return build_rich_section(
            title="RESULT",
            renderables=[
                status_text,
                Text("All expected SSIDs are confirmed.", style=get_rich_style("white")),
            ],
            border_style=get_rich_style("white"),
        )

    failure_ssids = trace_verdict.get("failure_ssids", [])
    status_text = Text("Status               : ")
    status_text.append("FAILED", style=get_rich_style("red"))
    renderables = [
        status_text,
        Text(""),
        Text("Failure SSIDS", style=get_rich_style("white")),
    ]
    renderables.extend(get_failure_ssid_renderables(failure_ssids=failure_ssids))

    return build_rich_section(
        title="RESULT",
        renderables=renderables,
        border_style=get_rich_style("white"),
    )


def build_not_tested_result_section():
    status_text = Text("Status               : ")
    status_text.append("NOT TESTED", style=get_rich_style("white"))
    return build_rich_section(
        title="RESULT",
        renderables=[status_text],
        border_style=get_rich_style("white"),
    )


def print_trace_verdict(trace_verdict):
    get_rich_console().print(build_trace_verdict_section(trace_verdict=trace_verdict))
