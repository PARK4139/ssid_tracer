from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.resolve()
_SECTIONS = ["result", "detected", "statistics", "config"]


def _bootstrap(title: str) -> str:
    return f"call _pane_bootstrap.cmd {title}"


def _section_command(section: str) -> list[str]:
    return [
        "--title", section,
        "-d", str(_PROJECT_ROOT),
        "cmd.exe", "/k", _bootstrap(section).replace(";", r"\;"),
    ]


def _get_windows_terminal_arguments() -> list[str]:
    args = [
        "new-tab",
        *_section_command("result"),
        ";",
        "split-pane", "-V", "--size", "0.75",
        *_section_command("detected"),
        ";",
        "split-pane", "-V", "--size", "0.6667",
        *_section_command("statistics"),
        ";",
        "split-pane", "-V", "--size", "0.5",
        *_section_command("config"),
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
