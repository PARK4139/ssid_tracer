import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = PROJECT_ROOT / "launch_panes.py"


def load_launcher_module():
    spec = importlib.util.spec_from_file_location(
        "windows_terminal_launcher",
        LAUNCHER_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_windows_terminal_arguments_create_expected_section_panes():
    launcher = load_launcher_module()

    args = launcher._get_windows_terminal_arguments()

    assert args.count("new-tab") == 1
    assert args.count("split-pane") == 3
    assert args.count("--size") == 3
    assert args.count("0.5") == 3
    assert "0.6667" not in args
    assert args.count("move-focus") == 2
    assert "left" in args
    assert "right" in args
    assert args.count("-V") == 1
    assert args.count("-H") == 2
    assert args.count("result") == 2
    assert args.count("detected") == 2
    assert args.count("statistics") == 2
    assert args.count("config") == 2
    assert args.index("config") < args.index("result")
    assert args.index("-V") < args.index("left")
    assert args.index("left") < args.index("result")
    assert args.index("result") < args.index("right")
    assert args.index("right") < args.index("statistics")
    assert args.index("config") < args.index("detected")
    assert "cmd.exe" not in args
    assert "/k" not in args


def test_windows_terminal_arguments_launch_tracer_directly_in_every_pane():
    launcher = load_launcher_module()

    args = launcher._get_windows_terminal_arguments(python_exe="C:\\Python\\python.exe")

    assert args.count("C:\\Python\\python.exe") == 4
    assert args.count(str(PROJECT_ROOT / "ensure_wifi_expected_ssids_watched.py")) == 4
    assert args.count("--section") == 4
    assert "_pane_bootstrap.cmd" not in args


def test_cmd_launchers_delegate_to_python_launcher():
    for filename in [
        "run.cmd",
        "개발.windows_terminal_실행_as_lateral_panes.cmd",
    ]:
        text = (PROJECT_ROOT / filename).read_text(encoding="utf-8")

        assert 'python "%~dp0launch_panes.py"' in text
        assert "split-pane" not in text
        assert "_pane_bootstrap.cmd" not in text


def test_pane_bootstrap_starts_requested_tracer_section():
    text = (PROJECT_ROOT / "_pane_bootstrap.cmd").read_text(encoding="utf-8")

    assert "title %~1" in text
    assert "SSID_TRACER_PYTHON_EXE" in text
    assert 'set "PYTHON_EXE=python"' in text
    assert "VIRTUAL_ENV" not in text
    assert '"%PYTHON_EXE%" ensure_wifi_expected_ssids_watched.py --section %~1' in text
    assert "exited with %ERRORLEVEL%" in text


def test_launcher_passes_python_with_rich_to_panes():
    text = LAUNCHER_PATH.read_text(encoding="utf-8")

    assert "_reset_selected_ssid_config()" in text
    assert "def _find_python_with_rich()" in text
    assert "[python_exe, \"-c\", \"import rich\"]" in text
    assert "args = _get_windows_terminal_arguments(python_exe=python_exe)" in text
    assert "subprocess.Popen([wt, *args])" in text


def test_launcher_resets_selected_config_before_opening_panes(tmp_path):
    launcher = load_launcher_module()
    selected_config_path = tmp_path / "selected_ssid_config.txt"
    selected_config_path.write_text("config_26_ssids_for_exhivition", encoding="utf-8")

    launcher._SELECTED_SSID_CONFIG_PATH = selected_config_path
    launcher._reset_selected_ssid_config()

    assert not selected_config_path.exists()


def test_python_detector_finds_interpreter_with_rich():
    launcher = load_launcher_module()

    python_exe = launcher._find_python_with_rich()

    assert launcher._can_import_rich(python_exe)
