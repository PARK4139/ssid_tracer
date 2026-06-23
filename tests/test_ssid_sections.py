from pathlib import Path

import pytest
from rich.console import Console

import ssid_analyzer
import ssid_config
from ssid_utils import get_unique_ssids
from ssid_renderer import build_result_screen
from ssid_renderer_detected import build_detected_ssid_section
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
            config_name="config_55_ssids_for_deprecated",
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

    assert "# RESULT" in text
    assert "Selected Config                :" in text
    assert "config_55_ssids_for_deprecated" in text
    assert "# LIVE SSIDS" not in text
    assert "# STATISTICS" not in text
    assert "# CONFIG" not in text


def test_detected_section_only_renders_detected_panel():
    text = build_text_for_section("detected")

    assert "# LIVE SSIDS(2)" in text
    assert "PRODUCT_5G INTENDED band=5G ch=36" in text
    assert "PRODUCT_2G INTENDED band=2_4G ch=6" in text
    assert "bssid_count" not in text
    assert "# RESULT" not in text
    assert "# STATISTICS" not in text
    assert "# CONFIG" not in text


def test_empty_detected_section_title_includes_zero_count():
    text = render_text(
        build_detected_ssid_section(
            live_confirmed_5g_ssids=[],
            live_confirmed_2_4g_ssids=[],
            dead_confirmed_5g_ssids=[],
            dead_confirmed_2_4g_ssids=[],
            dead_detected_wifi_entries=[],
            action_required_items=[],
            ignored_detected_wifi_entries=[],
            planned_ssids=[],
        )
    )

    assert "# LIVE SSIDS(0)" in text


def test_live_ssids_section_excludes_missing_and_dead_rows():
    text = render_text(
        build_detected_ssid_section(
            live_confirmed_5g_ssids=[],
            live_confirmed_2_4g_ssids=[],
            dead_confirmed_5g_ssids=["DEAD_5G"],
            dead_confirmed_2_4g_ssids=["DEAD_2G"],
            dead_detected_wifi_entries=[
                {
                    "ssid": "DEAD_DETECTED",
                    "band": "5G",
                    "channels": [36],
                    "bssid_count": 1,
                }
            ],
            action_required_items=[
                {
                    "status_label": "MISSING_5G",
                    "ssid": "MISSING_5G",
                    "band": "5G",
                    "channel": "",
                },
                {
                    "status_label": "NOT_CONFIRMED_5G",
                    "ssid": "LIVE_UNEXPECTED",
                    "band": "5G",
                    "channel": "36",
                },
            ],
            ignored_detected_wifi_entries=[],
            planned_ssids=[],
        )
    )

    assert "# LIVE SSIDS(1)" in text
    assert "LIVE_UNEXPECTED Unexpected band=5G ch=36" in text
    assert "MISSING_5G" not in text
    assert "DEAD_5G" not in text
    assert "DEAD_2G" not in text
    assert "DEAD_DETECTED" not in text


def test_statistics_section_only_renders_statistics_panel():
    text = build_text_for_section("statistics")

    assert "# STATISTICS" in text
    assert "# RESULT" not in text
    assert "# LIVE SSIDS" not in text
    assert "# CONFIG" not in text


def test_config_section_only_renders_config_panel():
    text = build_text_for_section("config")

    assert "# CONFIG" in text
    assert "Intended(2)" in text
    assert "Expected(" not in text
    assert "Expected 5G" not in text
    assert "# RESULT" not in text
    assert "# LIVE SSIDS" not in text
    assert "# STATISTICS" not in text


def test_config_section_renders_intended_and_ignored_counts_without_planned():
    text = build_text_for_section("config")

    assert "Intended(2)" in text
    assert "01. PRODUCT_5G" in text
    assert "02. PRODUCT_2G" in text
    assert "Planned" not in text
    assert "PLANNED_WIFI" not in text
    assert "Ignored(1)" in text
    assert "01. OFFICE" in text
    assert "Expected 2.4G" not in text
    assert "Expected(" not in text
    assert "  - " not in text


def test_config_55_ssids_for_deprecated_has_55_expected_ssids_and_expected_inclusions():
    selected_config = ssid_config.SSID_CONFIGS["config_55_ssids_for_deprecated"]
    expected_5g_ssids = get_unique_ssids(
        raw_ssids=selected_config["expected_5g_ssids"],
        skip_tbd=ssid_config.SKIP_TBD,
    )
    expected_2_4g_ssids = get_unique_ssids(
        raw_ssids=selected_config["expected_2_4g_ssids"],
        skip_tbd=ssid_config.SKIP_TBD,
    )

    assert len(expected_5g_ssids) + len(expected_2_4g_ssids) == 55
    assert "MERCUSYS_BA30_5G" in expected_5g_ssids
    assert "MERCUSYS_C027_5G" in expected_5g_ssids
    assert "MERCUSYS_C027" in expected_2_4g_ssids
    assert "Keenetic-1947" not in expected_5g_ssids
    assert "Keenetic-1947" not in expected_2_4g_ssids


def test_config_26_ssids_for_exhivition_uses_13_expected_pairs_with_5g_suffix_for_same_names():
    selected_config = ssid_config.SSID_CONFIGS["config_26_ssids_for_exhivition"]

    assert selected_config["expected_5g_ssids"] == [
        "ASUS_F6_5G",
        "NETGEAR11-5G",
        "NETGEAR56-5G",
        "Tenda_EFFAA0_5G",
        "TP-Link_A2B2_5G",
        "TP-Link_35E8_5G",
        "TP-Link_5GHz_138BD2",
        "TP-Link_3B54_5G",
        "ASUS_00_EBR63_5G",
        "ASUS_C8_5G",
        "ASUS_60_5G",
        "Tenda_EFE220_5G",
        "Linksys00711_5G",
    ]
    assert selected_config["expected_2_4g_ssids"] == [
        "ASUS_F6",
        "NETGEAR11",
        "NETGEAR56",
        "Tenda_EFFAA0",
        "TP-Link_A2B2",
        "TP-Link_35E8",
        "TP-Link_2.4GHz_138BD1",
        "TP-Link_3B54",
        "ASUS_00_EBR63",
        "ASUS_C8",
        "ASUS_60",
        "Tenda_EFE220",
        "Linksys00711",
    ]


def test_config_2_ssids_variants_are_available_for_e8e4_mesh_networking_and_eb98():
    assert ssid_config.SSID_CONFIGS["config_2_ssids_as_e8e4_for_mesh_networking"]["expected_5g_ssids"] == [
        "TP-Link_E8E4_5G"
    ]
    assert ssid_config.SSID_CONFIGS["config_2_ssids_as_e8e4_for_mesh_networking"]["expected_2_4g_ssids"] == [
        "TP-Link_E8E4"
    ]
    assert ssid_config.SSID_CONFIGS["config_2_ssids_as_eb98_for_room_seperating"]["expected_5g_ssids"] == [
        "TP-Link_EB98_5G"
    ]
    assert ssid_config.SSID_CONFIGS["config_2_ssids_as_eb98_for_room_seperating"]["expected_2_4g_ssids"] == [
        "TP-Link_EB98"
    ]


def test_config_2_ssids_as_eb98_for_room_seperating_ignores_neighbor_room_ssids():
    ignored_ssids = ssid_config.SSID_CONFIGS["config_2_ssids_as_eb98_for_room_seperating"]["ignored_ssids"]

    for ssid in [
        "iptime5G",
        "MERCUSYS_BA30_5G",
        "TP-Link_E8E4_5G",
        "iptime",
        "MERCUSYS_BA30",
        "TP-Link_E8E4",
    ]:
        assert ssid in ignored_ssids


def test_missing_selected_config_returns_not_tested_result_pane(monkeypatch):
    selected_config_path = ssid_config.SELECTED_SSID_CONFIG_PATH
    original_config_text = selected_config_path.read_text(encoding="utf-8") if selected_config_path.exists() else None

    try:
        if selected_config_path.exists():
            selected_config_path.unlink()

        monkeypatch.setattr(tracer, "clear_console", lambda: None)
        current_ssid_configuration = tracer.get_current_ssid_configuration()
        console = Console(record=True, width=160, no_color=True)
        tracer.print_current_result_screen(
            console=console,
            current_ssid_configuration=current_ssid_configuration,
            detected_wifi_entries=[],
            scan_ok=False,
            scan_message="scan pending",
            error_message="",
            section_name="result",
        )
        text = console.export_text()
    finally:
        if original_config_text is None:
            if selected_config_path.exists():
                selected_config_path.unlink()
        else:
            tracer.ensure_selected_ssid_config_name_written(ssid_config_name=original_config_text)

    assert current_ssid_configuration["config_name"] is None
    assert current_ssid_configuration["expected_5g_ssids"] == []
    assert "RESULT" in text
    assert "Status               : NOT TESTED" in text
    assert "Selected Config                :" in text
    assert "NOT SET" in text
    assert '"NOT TESTED"' not in text


def test_missing_selected_config_non_result_panes_do_not_render_result_panel(monkeypatch):
    selected_config_path = ssid_config.SELECTED_SSID_CONFIG_PATH
    original_config_text = selected_config_path.read_text(encoding="utf-8") if selected_config_path.exists() else None

    try:
        if selected_config_path.exists():
            selected_config_path.unlink()

        monkeypatch.setattr(tracer, "clear_console", lambda: None)
        current_ssid_configuration = tracer.get_current_ssid_configuration()

        expected_titles_by_section = {
            "detected": "LIVE SSIDS(0)",
            "statistics": "STATISTICS",
            "config": "CONFIG",
        }

        for section_name, expected_title in expected_titles_by_section.items():
            console = Console(record=True, width=160, no_color=True)
            tracer.print_current_result_screen(
                console=console,
                current_ssid_configuration=current_ssid_configuration,
                detected_wifi_entries=[],
                scan_ok=False,
                scan_message="scan pending",
                error_message="",
                section_name=section_name,
            )
            text = console.export_text()

            assert expected_title in text
            assert "RESULT" not in text
    finally:
        if original_config_text is None:
            if selected_config_path.exists():
                selected_config_path.unlink()
        else:
            tracer.ensure_selected_ssid_config_name_written(ssid_config_name=original_config_text)


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


def test_config_section_prompts_interactively_inside_refresh_loop(monkeypatch):
    calls = []

    monkeypatch.setattr(tracer, "ensure_ansi_color_enabled", lambda: None)
    monkeypatch.setattr(tracer, "setup_console_drag", lambda: None)
    monkeypatch.setattr(tracer, "get_rich_console", lambda: Console(record=True, width=160, no_color=True))
    monkeypatch.setattr(tracer, "print_current_result_screen", lambda **_kwargs: None)
    monkeypatch.setattr(
        tracer,
        "get_current_ssid_configuration",
        lambda: {
            "config_name": "config_55_ssids_for_deprecated",
            "expected_5g_ssids": ["A_5G"],
            "expected_2_4g_ssids": ["A"],
            "ignored_ssids": [],
            "planned_ssids": [],
        },
    )

    def raise_after_prompt():
        calls.append("prompted")
        raise KeyboardInterrupt

    monkeypatch.setattr(tracer, "ensure_ssid_config_selected_interactively", raise_after_prompt)

    with pytest.raises(KeyboardInterrupt):
        tracer.ensure_wifi_expected_ssids_watched(section_name="config")

    assert calls == ["prompted"]


def test_config_prompt_mentions_tab_completion(monkeypatch):
    prompts = []

    def fake_ensure_value_completed(value, choices, prompt_message):
        prompts.append(prompt_message)
        return choices[0]

    monkeypatch.setattr(tracer, "ensure_value_completed", fake_ensure_value_completed)
    monkeypatch.setattr(tracer, "ensure_selected_ssid_config_name_written", lambda ssid_config_name: ssid_config_name)

    tracer.ensure_ssid_config_selected_interactively()

    assert prompts == ["Config(Press Tab)> "]
