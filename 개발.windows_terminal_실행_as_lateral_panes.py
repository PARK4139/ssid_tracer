from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.resolve()
_VENV_DIR = _PROJECT_ROOT / ".venv"
_VENV_SCRIPTS = _VENV_DIR / "Scripts"

_SECTIONS = ["result", "detected", "statistics", "config"]


def _bootstrap(title: str) -> str:
    return f'call "{_PROJECT_ROOT / "_pane_bootstrap.cmd"}" {title}'


def _get_windows_terminal_arguments() -> list[str]:
    args = [
        "new-tab",
        "-d", str(_PROJECT_ROOT),
        "cmd.exe", "/k", _bootstrap("result").replace(";", r"\;"),
        ";",
        "split-pane", "-H", "--size", "0.5",
        "-d", str(_PROJECT_ROOT),
        "cmd.exe", "/k", _bootstrap("detected").replace(";", r"\;"),
        ";",
        "split-pane", "-V", "--size", "0.5",
        "-d", str(_PROJECT_ROOT),
        "cmd.exe", "/k", _bootstrap("config").replace(";", r"\;"),
        ";",
        "move-focus", "left",
        ";",
        "split-pane", "-V", "--size", "0.5",
        "-d", str(_PROJECT_ROOT),
        "cmd.exe", "/k", _bootstrap("statistics").replace(";", r"\;"),
    ]

    return args


def _find_windows_terminal() -> str:
    import os
    import shutil

    preferred = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "wt.exe"
    if preferred.exists():
        return str(preferred)

    fallback = shutil.which("wt.exe")
    if fallback:
        return fallback

    raise FileNotFoundError("Windows Terminal executable not found.")


def _run_main() -> None:
    import subprocess

    wt = _find_windows_terminal()
    args = _get_windows_terminal_arguments()
    subprocess.Popen([wt, *args])


if __name__ == "__main__":
    _run_main()
