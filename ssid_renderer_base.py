from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.console import Group

from ssid_config import (
    ANSI_GRAY,
    ANSI_GREEN,
    ANSI_ORANGE,
    ANSI_RED,
    ANSI_RESET,
    ENABLE_ANSI_COLOR,
)


def get_rich_console():
    return Console(no_color=not ENABLE_ANSI_COLOR)


def get_rich_style(color_name):
    return {
        "green": "green",
        "gray": "bright_black",
        "red": "red",
        "orange": "orange3",
        "white": "white",
    }.get(color_name, "")


def build_rich_section(title, renderables, border_style="white"):
    if len(renderables) <= 0:
        renderables = [Text("  01.")]
    return Panel(
        Group(*renderables),
        title=title,
        border_style=border_style,
        box=box.ASCII,
    )


def print_rich_section(title, renderables, border_style="white"):
    get_rich_console().print(
        build_rich_section(title=title, renderables=renderables, border_style=border_style)
    )


def get_red_text(text):
    if not ENABLE_ANSI_COLOR:
        return text
    return f"{ANSI_RED}{text}{ANSI_RESET}"


def get_green_text(text):
    if not ENABLE_ANSI_COLOR:
        return text
    return f"{ANSI_GREEN}{text}{ANSI_RESET}"


def get_gray_text(text):
    if not ENABLE_ANSI_COLOR:
        return text
    return f"{ANSI_GRAY}{text}{ANSI_RESET}"


def get_orange_text(text):
    if not ENABLE_ANSI_COLOR:
        return text
    return f"{ANSI_ORANGE}{text}{ANSI_RESET}"


def get_colored_text(text, color_name):
    if color_name == "green":
        return get_green_text(text)
    if color_name == "gray":
        return get_gray_text(text)
    if color_name == "red":
        return get_red_text(text)
    if color_name == "orange":
        return get_orange_text(text)
    return text
