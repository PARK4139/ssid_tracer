import contextlib
import io
import unittest

import ensure_wifi_expected_ssids_watched as tracer


def wifi_entry(ssid, bssid, channel):
    return {
        "ssid": ssid,
        "bssid": bssid,
        "channel": channel,
        "band": tracer.get_band_from_channel(
            channel=channel,
        ),
    }


class WifiSsidTracerTestCase(unittest.TestCase):
    def setUp(self):
        tracer.EVER_LIVE_CONFIRMED_SSID_BAND_SET.clear()
        tracer.EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY.clear()

    def tearDown(self):
        tracer.EVER_LIVE_CONFIRMED_SSID_BAND_SET.clear()
        tracer.EVER_DETECTED_WIFI_ENTRY_BY_GROUP_KEY.clear()

    def get_check_result(self, expected_5g_ssids, expected_2_4g_ssids, detected_wifi_entries):
        return tracer.get_check_result(
            expected_5g_ssids=expected_5g_ssids,
            expected_2_4g_ssids=expected_2_4g_ssids,
            ignored_ssids=[],
            detected_wifi_entries=detected_wifi_entries,
        )

    def get_trace_verdict(self, expected_5g_ssids, expected_2_4g_ssids, detected_wifi_entries, scan_ok=True, scan_message="scan ok", error_message=""):
        (
            live_confirmed_5g_ssids,
            live_confirmed_2_4g_ssids,
            dead_confirmed_5g_ssids,
            dead_confirmed_2_4g_ssids,
            _dead_detected_wifi_entries,
            action_required_items,
            _ignored_detected_wifi_entries,
        ) = self.get_check_result(
            expected_5g_ssids=expected_5g_ssids,
            expected_2_4g_ssids=expected_2_4g_ssids,
            detected_wifi_entries=detected_wifi_entries,
        )

        return tracer.get_trace_verdict(
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

    def test_trace_verdict_passes_when_all_expected_ssids_are_confirmed(self):
        trace_verdict = self.get_trace_verdict(
            expected_5g_ssids=["PRODUCT_5G"],
            expected_2_4g_ssids=["PRODUCT_2G"],
            detected_wifi_entries=[
                wifi_entry("PRODUCT_5G", "00:00:00:00:00:01", 36),
                wifi_entry("PRODUCT_2G", "00:00:00:00:00:02", 6),
            ],
        )

        self.assertEqual(
            trace_verdict["status_label"],
            "PASSED",
        )
        self.assertEqual(
            tracer.get_trace_verdict_text(trace_verdict),
            "PASSED",
        )

    def test_print_result_splits_detected_ssids_and_result_sections(self):
        original_enable_ansi_color = tracer.ENABLE_ANSI_COLOR
        original_system = tracer.os.system
        output_buffer = io.StringIO()

        tracer.ENABLE_ANSI_COLOR = False
        tracer.os.system = lambda _command: self.fail("print_result should not clear the console")

        try:
            with contextlib.redirect_stdout(output_buffer):
                tracer.print_result(
                    config_name="config_55_ssids",
                    expected_5g_ssids=["PRODUCT_5G"],
                    expected_2_4g_ssids=["PRODUCT_2G"],
                    ignored_ssids=[],
                    planned_ssids=[],
                    detected_wifi_entries=[
                        wifi_entry("PRODUCT_5G", "00:00:00:00:00:01", 36),
                        wifi_entry("PRODUCT_2G", "00:00:00:00:00:02", 6),
                    ],
                    scan_ok=True,
                    scan_message="scan ok",
                    error_message="",
                )
        finally:
            tracer.ENABLE_ANSI_COLOR = original_enable_ansi_color
            tracer.os.system = original_system

        output_text = output_buffer.getvalue()

        self.assertIn(
            "LIVE SSIDS",
            output_text,
        )
        self.assertIn(
            "RESULT",
            output_text,
        )
        self.assertIn(
            "PASSED",
            output_text,
        )
        self.assertLess(
            output_text.index("RESULT"),
            output_text.index("LIVE SSIDS"),
        )

    def test_print_trace_verdict_lists_failure_ssids(self):
        original_enable_ansi_color = tracer.ENABLE_ANSI_COLOR
        output_buffer = io.StringIO()

        tracer.ENABLE_ANSI_COLOR = False

        try:
            with contextlib.redirect_stdout(output_buffer):
                tracer.print_trace_verdict(
                    {
                        "status_label": "FAILED",
                        "failure_reasons": [
                            "missing expected 5G SSID(s): PRODUCT_5G",
                            "unexpected 2.4G SSID(s): NEIGHBOR_WIFI(channel=6)",
                        ],
                        "failure_ssids": [
                            {"status_label": "MISSING", "ssid": "PRODUCT_5G"},
                            {"status_label": "UNEXPECTED", "ssid": "NEIGHBOR_WIFI(channel=6)"},
                        ],
                    }
                )
        finally:
            tracer.ENABLE_ANSI_COLOR = original_enable_ansi_color

        output_text = output_buffer.getvalue()

        self.assertIn("Failure SSIDS", output_text)
        self.assertIn("01. [MISSING] PRODUCT_5G", output_text)
        self.assertIn("02. [UNEXPECTED] NEIGHBOR_WIFI(channel=6)", output_text)
        self.assertNotIn("Failure Reason Count", output_text)
        self.assertNotIn("Failure Reasons", output_text)

    def test_trace_verdict_fails_with_unexpected_ssid_reason(self):
        trace_verdict = self.get_trace_verdict(
            expected_5g_ssids=["PRODUCT_5G"],
            expected_2_4g_ssids=[],
            detected_wifi_entries=[
                wifi_entry("PRODUCT_5G", "00:00:00:00:00:01", 36),
                wifi_entry("NEIGHBOR_WIFI", "00:00:00:00:00:02", 6),
            ],
        )
        verdict_text = tracer.get_trace_verdict_text(
            trace_verdict=trace_verdict,
        )

        self.assertEqual(
            trace_verdict["status_label"],
            "FAILED",
        )
        self.assertIn(
            "unexpected SSID(s): NEIGHBOR_WIFI(channel=6)",
            verdict_text,
        )
        self.assertIn(
            "confirmed expected count: 1/1",
            verdict_text,
        )
        self.assertIn(
            {"status_label": "UNEXPECTED", "ssid": "NEIGHBOR_WIFI(channel=6)"},
            trace_verdict["failure_ssids"],
        )

    def test_trace_verdict_fails_with_missing_expected_ssid_reason(self):
        trace_verdict = self.get_trace_verdict(
            expected_5g_ssids=["PRODUCT_5G"],
            expected_2_4g_ssids=["PRODUCT_2G"],
            detected_wifi_entries=[
                wifi_entry("PRODUCT_2G", "00:00:00:00:00:02", 6),
            ],
        )
        verdict_text = tracer.get_trace_verdict_text(
            trace_verdict=trace_verdict,
        )

        self.assertEqual(
            trace_verdict["status_label"],
            "FAILED",
        )
        self.assertIn(
            "missing expected SSID(s): PRODUCT_5G",
            verdict_text,
        )
        self.assertIn(
            "confirmed expected count: 1/2",
            verdict_text,
        )
        self.assertIn(
            {"status_label": "MISSING", "ssid": "PRODUCT_5G"},
            trace_verdict["failure_ssids"],
        )

    def test_trace_verdict_fails_with_dead_confirmed_ssid_reason(self):
        self.get_trace_verdict(
            expected_5g_ssids=["PRODUCT_5G"],
            expected_2_4g_ssids=[],
            detected_wifi_entries=[
                wifi_entry("PRODUCT_5G", "00:00:00:00:00:01", 36),
            ],
        )

        trace_verdict = self.get_trace_verdict(
            expected_5g_ssids=["PRODUCT_5G"],
            expected_2_4g_ssids=[],
            detected_wifi_entries=[],
            scan_ok=False,
            scan_message="WlanScan failed for all interfaces",
            error_message="netsh returned no networks",
        )
        verdict_text = tracer.get_trace_verdict_text(
            trace_verdict=trace_verdict,
        )

        self.assertEqual(
            trace_verdict["status_label"],
            "FAILED",
        )
        self.assertIn(
            "previously confirmed SSID(s) not visible now: PRODUCT_5G",
            verdict_text,
        )
        self.assertIn(
            "scan/read error: netsh returned no networks",
            verdict_text,
        )
        self.assertIn(
            "scan warning: WlanScan failed for all interfaces",
            verdict_text,
        )
        self.assertIn(
            {"status_label": "DEAD", "ssid": "PRODUCT_5G"},
            trace_verdict["failure_ssids"],
        )

    def test_not_confirmed_entries_are_grouped_by_ssid_and_band(self):
        (
            _live_confirmed_5g_ssids,
            _live_confirmed_2_4g_ssids,
            _dead_confirmed_5g_ssids,
            _dead_confirmed_2_4g_ssids,
            _dead_detected_wifi_entries,
            action_required_items,
            _ignored_detected_wifi_entries,
        ) = self.get_check_result(
            expected_5g_ssids=[],
            expected_2_4g_ssids=[],
            detected_wifi_entries=[
                wifi_entry("NEIGHBOR_WIFI", "00:00:00:00:00:01", 1),
                wifi_entry("NEIGHBOR_WIFI", "00:00:00:00:00:02", 1),
                wifi_entry("NEIGHBOR_WIFI", "00:00:00:00:00:03", 6),
            ],
        )

        self.assertEqual(
            action_required_items,
            [
                {
                    "status_label": "NOT_CONFIRMED_2_4G",
                    "ssid": "NEIGHBOR_WIFI",
                    "band": "2_4G",
                    "channel": "1, 6",
                    "reason": "Detected 2.4GHz SSID but not in expected 2.4GHz list; bssid_count=3",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
