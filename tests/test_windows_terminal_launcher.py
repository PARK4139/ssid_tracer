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
    assert "0.75" in args
    assert "0.6667" in args
    assert "0.5" in args
    assert "move-focus" not in args
    assert args.count("-V") == 3
    assert "-H" not in args
    joined_args = "\n".join(args)
    assert joined_args.count(" result") == 1
    assert joined_args.count(" detected") == 1
    assert joined_args.count(" statistics") == 1
    assert joined_args.count(" config") == 1
    assert args.count("cmd.exe") == 4
    assert args.count("/k") == 4


def test_windows_terminal_arguments_launch_bootstrap_in_every_pane():
    launcher = load_launcher_module()

    args = launcher._get_windows_terminal_arguments()
    pane_commands = [
        args[index + 2]
        for index, value in enumerate(args)
        if value == "cmd.exe"
    ]

    assert len(pane_commands) == 4
    for command in pane_commands:
        assert "_pane_bootstrap.cmd" in command
        assert command.startswith("call _pane_bootstrap.cmd ")
        assert '"' not in command


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
    assert 'set "PYTHON_EXE=python"' in text
    assert "VIRTUAL_ENV" not in text
    assert '"%PYTHON_EXE%" ensure_wifi_expected_ssids_watched.py --section %~1' in text
    assert "exited with %ERRORLEVEL%" in text
