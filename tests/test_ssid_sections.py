from pathlib import Path

from rich.console import Console

import ssid_analyzer
import ssid_config
from ssid_renderer import build_result_screen
import ensure_wifi_expected_ssids_watched as tracer


def render_text(renderable):
    console = Console(record=True, width=160, no_color=True)
    console.print(renderable)
    return console.export_text()


def wifi_entry(ssid, bssid, channel, band):
    return {
        "ssid": ssid,
        "bssid": bssid,
        "channel": channel,
        "band": band,
    }


def build_text_for_section(section_name):
    ssid_analyzer.EVER_LIVE_CONFIRMED_SSID_BAND_SET.clear()
    ssid_analyzer.EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY.clear()
    return render_text(
        build_result_screen(
            expected_5g_ssids=["PRODUCT_5G"],
            expected_2_4g_ssids=["PRODUCT_2G"],
            ignored_ssids=["OFFICE"],
            planned_ssids=["PLANNED_WIFI"],
            detected_wifi_entries=[
                wifi_entry("PRODUCT_5G", "00:00:00:00:00:01", 36, "5G"),
                wifi_entry("PRODUCT_2G", "00:00:00:00:00:02", 6, "2_4G"),
            ],
            scan_ok=True,
            scan_message="scan ok",
            error_message="",
            section_name=section_name,
        )
    )


def test_result_section_only_renders_result_panel():
    text = build_text_for_section("result")

    assert "RESULT" in text
    assert "DETECTED SSID" not in text
    assert "STATISTICS" not in text
    assert "CONFIG" not in text


def test_detected_section_only_renders_detected_panel():
    text = build_text_for_section("detected")

    assert "DETECTED SSID" in text
    assert "RESULT" not in text
    assert "STATISTICS" not in text
    assert "CONFIG" not in text


def test_statistics_section_only_renders_statistics_panel():
    text = build_text_for_section("statistics")

    assert "STATISTICS" in text
    assert "RESULT" not in text
    assert "DETECTED SSID" not in text
    assert "CONFIG" not in text


def test_config_section_only_renders_config_panel():
    text = build_text_for_section("config")

    assert "CONFIG" in text
    assert "Expected 5G Count" in text
    assert "RESULT" not in text
    assert "DETECTED SSID" not in text
    assert "STATISTICS" not in text


def test_refresh_loop_does_not_use_rich_live_alternate_screen():
    source_path = Path(tracer.__file__)
    source = source_path.read_text(encoding="utf-8")

    assert "from rich.live import Live" not in source
    assert "screen=True" not in source


def test_refresh_loop_runs_cls_before_each_print_and_uses_three_second_interval():
    source_path = Path(tracer.__file__)
    source = source_path.read_text(encoding="utf-8")

    assert 'os.system("cls")' in source
    assert "clear_console()" in source
    assert ssid_config.WATCH_INTERVAL_SEC == 3.0
