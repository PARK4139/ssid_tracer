from pathlib import Path

from rich.console import Console

import ssid_analyzer
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


def test_live_display_does_not_use_alternate_screen_for_scrollback():
    source_path = Path(tracer.__file__)
    source = source_path.read_text(encoding="utf-8")

    assert "screen=False" in source
    assert "screen=True" not in source
    assert 'vertical_overflow="visible"' in source
