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
    import os
    import subprocess

    wt = _find_windows_terminal()
    args = _get_windows_terminal_arguments()
    env = os.environ.copy()
    env["SSID_TRACER_PYTHON_EXE"] = _find_python_with_rich()
    subprocess.Popen([wt, *args], env=env)


if __name__ == "__main__":
    _run_main()
