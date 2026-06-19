from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.resolve()
_SECTIONS = ["result", "detected", "statistics", "config"]


def _section_command(section: str, python_exe: str) -> list[str]:
    return [
        "--title", section,
        "-d", str(_PROJECT_ROOT),
        python_exe,
        str(_PROJECT_ROOT / "ensure_wifi_expected_ssids_watched.py"),
        "--section", section,
    ]


def _get_windows_terminal_arguments(python_exe: str = "python") -> list[str]:
    args = [
        "new-tab",
        *_section_command("result", python_exe),
        ";",
        "split-pane", "-V", "--size", "0.75",
        *_section_command("detected", python_exe),
        ";",
        "split-pane", "-V", "--size", "0.6667",
        *_section_command("statistics", python_exe),
        ";",
        "split-pane", "-V", "--size", "0.5",
        *_section_command("config", python_exe),
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


def _get_python_candidates() -> list[str]:
    import shutil
    import subprocess
    import sys

    candidates = [sys.executable]

    path_python = shutil.which("python")
    if path_python:
        candidates.append(path_python)

    known_project_python = Path.home() / "Downloads" / "pk_system" / ".venv" / "Scripts" / "python.exe"
    if known_project_python.exists():
        candidates.append(str(known_project_python))

    try:
        where_result = subprocess.run(
            ["where.exe", "python"],
            check=False,
            capture_output=True,
            text=True,
        )
        candidates.extend(
            line.strip()
            for line in where_result.stdout.splitlines()
            if line.strip()
        )
    except OSError:
        pass

    unique_candidates = []
    seen = set()
    for candidate in candidates:
        normalized = str(Path(candidate))
        if normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        unique_candidates.append(normalized)

    return unique_candidates


def _can_import_rich(python_exe: str) -> bool:
    import subprocess

    try:
        result = subprocess.run(
            [python_exe, "-c", "import rich"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0


def _find_python_with_rich() -> str:
    import sys

    for python_exe in _get_python_candidates():
        if _can_import_rich(python_exe=python_exe):
            return python_exe

    return sys.executable


def _run_main() -> None:
    import subprocess

    wt = _find_windows_terminal()
    python_exe = _find_python_with_rich()
    args = _get_windows_terminal_arguments(python_exe=python_exe)
    subprocess.Popen([wt, *args])


if __name__ == "__main__":
    _run_main()
